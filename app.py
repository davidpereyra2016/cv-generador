from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response
import mercadopago
import os
from dotenv import load_dotenv
from datetime import datetime
import base64
from io import BytesIO
from fpdf import FPDF
import tempfile

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de directorios
if not os.getenv('VERCEL_ENV'):
    # En desarrollo local
    UPLOAD_FOLDER = 'static/uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    PDF_FOLDER = 'bd_pdf'
    os.makedirs(PDF_FOLDER, exist_ok=True)
else:
    # En Vercel (producción)
    UPLOAD_FOLDER = tempfile.gettempdir()
    PDF_FOLDER = tempfile.gettempdir()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de MercadoPago
mp_access_token = os.getenv('MP_ACCESS_TOKEN')
mp_public_key = os.getenv('MP_PUBLIC_KEY')

if not mp_access_token or not mp_public_key:
    raise ValueError("MP_ACCESS_TOKEN y MP_PUBLIC_KEY deben estar configurados en las variables de entorno")

sdk = mercadopago.SDK(mp_access_token)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_preference', methods=['POST'])
def create_preference():
    try:
        data = request.get_json()
        
        # Crear el objeto de preferencia
        preference_data = {
            "items": [
                {
                    "title": "Generador de CV Profesional",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": 2000
                }
            ],
            "back_urls": {
                "success": request.host_url + "success",
                "failure": request.host_url + "failure",
                "pending": request.host_url + "pending"
            },
            "auto_return": "approved",
            "binary_mode": True
        }

        # Crear la preferencia en MercadoPago
        preference_response = sdk.preference().create(preference_data)
        
        if "response" not in preference_response:
            app.logger.error(f"Error en la respuesta de MercadoPago: {preference_response}")
            return jsonify({"error": "Error al crear la preferencia"}), 500
            
        return jsonify({
            "id": preference_response["response"]["id"],
            "init_point": preference_response["response"]["init_point"]
        })
            
    except Exception as e:
        app.logger.error(f"Error creating preference: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/success')
def success():
    template_type = request.args.get('template_type', 'basico')
    return render_template('success.html', template_type=template_type)

@app.route('/failure')
def failure():
    return "El pago falló"

@app.route('/pending')
def pending():
    return "El pago está pendiente"

@app.route('/get_mp_public_key', methods=['GET'])
def get_mp_public_key():
    return jsonify({"public_key": mp_public_key})

def generate_pdf_content(cv_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Configuración de fuentes
    pdf.set_font('Arial', 'B', 24)
    
    # Determinar el estilo de plantilla
    template_type = cv_data.get('template_type', 'basico')
    is_professional = template_type == 'profesional'
    
    # Configurar colores según la plantilla
    if is_professional:
        pdf.set_text_color(26, 73, 113)  # #1a4971
    else:
        pdf.set_text_color(51, 51, 51)  # #333333
    
    # Agregar imagen de perfil si existe
    if 'imagen_perfil' in cv_data and cv_data['imagen_perfil']:
        try:
            # Decodificar la imagen base64
            image_data = cv_data['imagen_perfil'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # Guardar temporalmente la imagen
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                tmp_img.write(image_bytes)
                img_path = tmp_img.name
            
            # Calcular posición de la imagen
            if is_professional:
                pdf.image(img_path, x=170, y=15, w=30, h=30)  # Más pequeña para diseño profesional
            else:
                pdf.image(img_path, x=160, y=15, w=40, h=40)  # Más grande para diseño básico
            
            # Limpiar archivo temporal
            os.remove(img_path)
        except Exception as e:
            app.logger.error(f"Error al procesar la imagen: {str(e)}")
    
    # Nombre
    pdf.set_xy(10, 20)
    pdf.cell(0, 20, cv_data['nombre'], ln=True, align='L')
    
    # Información de contacto
    pdf.set_font('Arial', '', 12)
    if is_professional:
        pdf.set_text_color(44, 62, 80)  # #2c3e50
    else:
        pdf.set_text_color(102, 102, 102)  # #666666
    
    if cv_data.get('email'):
        pdf.cell(0, 10, f"Email: {cv_data['email']}", ln=True)
    if cv_data.get('telefono'):
        pdf.cell(0, 10, f"Teléfono: {cv_data['telefono']}", ln=True)
    if cv_data.get('direccion'):
        pdf.cell(0, 10, f"Dirección: {cv_data['direccion']}", ln=True)
    if cv_data.get('dni'):
        pdf.cell(0, 10, f"DNI: {cv_data['dni']}", ln=True)
    if cv_data.get('fecha_nacimiento'):
        pdf.cell(0, 10, f"Fecha de nacimiento: {cv_data['fecha_nacimiento']}", ln=True)
    if cv_data.get('edad'):
        pdf.cell(0, 10, f"Edad: {cv_data['edad']}", ln=True)
    pdf.ln(10)
    
    # Experiencia laboral
    pdf.set_font('Arial', 'B', 16)
    if is_professional:
        pdf.set_text_color(26, 73, 113)
        pdf.set_fill_color(240, 242, 245)
    else:
        pdf.set_text_color(51, 51, 51)
        pdf.set_fill_color(248, 249, 250)
    
    pdf.cell(0, 10, 'Experiencia Laboral', ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    if is_professional:
        pdf.set_text_color(44, 62, 80)
    else:
        pdf.set_text_color(102, 102, 102)
    
    for exp in cv_data.get('experiencia', []):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"{exp['empresa']} - {exp['cargo']}", ln=True)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, exp['periodo'], ln=True)
        pdf.set_font('Arial', '', 11)
        pdf.multi_cell(0, 10, exp['descripcion'])
        pdf.ln(5)
    
    # Educación
    pdf.set_font('Arial', 'B', 16)
    if is_professional:
        pdf.set_text_color(26, 73, 113)
    else:
        pdf.set_text_color(51, 51, 51)
    
    pdf.cell(0, 10, 'Educación', ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    if is_professional:
        pdf.set_text_color(44, 62, 80)
    else:
        pdf.set_text_color(102, 102, 102)
    
    for edu in cv_data.get('educacion', []):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"{edu['institucion']} - {edu['titulo']}", ln=True)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, edu['periodo'], ln=True)
        pdf.ln(5)
    
    # Habilidades
    if cv_data.get('habilidades'):
        pdf.set_font('Arial', 'B', 16)
        if is_professional:
            pdf.set_text_color(26, 73, 113)
        else:
            pdf.set_text_color(51, 51, 51)
            
        pdf.cell(0, 10, 'Habilidades', ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 12)
        if is_professional:
            pdf.set_text_color(44, 62, 80)
        else:
            pdf.set_text_color(102, 102, 102)
            
        for skill in cv_data['habilidades']:
            pdf.cell(0, 10, f"• {skill}", ln=True)
    
    # Crear un archivo temporal para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
        pdf.output(pdf_path)
        return pdf_path

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        cv_data = data.get('cv_data')

        if not cv_data:
            return jsonify({'error': 'Datos incompletos'}), 400

        # Generar PDF
        pdf_path = generate_pdf_content(cv_data)

        # Enviar el archivo y luego eliminarlo
        response = send_file(pdf_path, as_attachment=True, download_name='cv.pdf')
        
        @response.call_on_close
        def cleanup():
            try:
                os.remove(pdf_path)
            except:
                pass
                
        return response

    except Exception as e:
        app.logger.error(f"Error generando PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.get_json()
        pdf_path = generate_pdf_content(data)
        
        # Enviar el archivo y luego eliminarlo
        response = send_file(pdf_path, as_attachment=True, download_name='cv.pdf')
        
        @response.call_on_close
        def cleanup():
            try:
                os.remove(pdf_path)
            except:
                pass
                
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # En desarrollo
    app.run(host='0.0.0.0', port=5000)
else:
    # En producción (Vercel)
    app = app.wsgi_app
