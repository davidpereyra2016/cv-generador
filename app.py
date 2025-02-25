from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response, current_app
import mercadopago
import os
from dotenv import load_dotenv
from datetime import datetime
import base64
from io import BytesIO
from fpdf import FPDF
import tempfile
import json
import uuid

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
        
        template_type = data.get("template_type", "basico")
        external_reference = data.get("external_reference")
        
        if template_type == "profesional":
            price = 2000
        else:
            price = 1500
        
        # Crear el objeto de preferencia
        preference_data = {
            "items": [
                {
                    "title": "Generador de CV Profesional",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": price
                }
            ],
            "back_urls": {
                "success": request.host_url + "success",
                "failure": request.host_url + "failure",
                "pending": request.host_url + "pending"
            },
            "auto_return": "approved",
            "binary_mode": True,
            "external_reference": external_reference
        }

        # Crear la preferencia en MercadoPago
        preference_response = sdk.preference().create(preference_data)
        
        if "response" not in preference_response:
            current_app.logger.error(f"Error en la respuesta de MercadoPago: {preference_response}")
            return jsonify({"error": "Error al crear la preferencia"}), 500
            
        return jsonify({
            "id": preference_response["response"]["id"],
            "init_point": preference_response["response"]["init_point"]
        })
            
    except Exception as e:
        current_app.logger.error(f"Error creating preference: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/save_form_data', methods=['POST'])
def save_form_data():
    try:
        form_data = request.get_json()
        
        # Generar un ID único para el formulario
        form_id = str(uuid.uuid4())
        
        # Crear el archivo JSON temporal
        json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, ensure_ascii=False)
            
        return jsonify({"form_id": form_id})
    except Exception as e:
        current_app.logger.error(f"Error saving form data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/success')
def success():
    try:
        # Obtener parámetros de la URL
        payment_id = request.args.get('payment_id')
        status = request.args.get('status')
        
        if status != 'approved':
            return redirect(url_for('failure'))
            
        # Registrar información del pago
        if payment_id:
            try:
                payment_info = sdk.payment().get(payment_id)
                if 'response' in payment_info:
                    current_app.logger.info(f"Pago confirmado: {payment_info['response']}")
                    
                    # Obtener el external_reference que contiene el form_id
                    form_id = payment_info['response'].get('external_reference')
                    
                    if form_id:
                        # Cargar datos del formulario
                        json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
                        if os.path.exists(json_path):
                            with open(json_path, 'r', encoding='utf-8') as f:
                                form_data = json.load(f)
                                
                            return render_template('success.html',
                                                template_type=form_data.get('template_type', 'basico'),
                                                payment_id=payment_id,
                                                form_id=form_id)
            except Exception as e:
                current_app.logger.error(f"Error al verificar pago: {str(e)}")
        
        return render_template('success.html',
                            template_type=request.args.get('template_type', 'basico'),
                            payment_id=payment_id)
        
    except Exception as e:
        current_app.logger.error(f"Error en success: {str(e)}")
        return str(e), 500

@app.route('/failure')
def failure():
    return "El pago falló"

@app.route('/pending')
def pending():
    return "El pago está pendiente"

@app.route('/get_mp_public_key', methods=['GET'])
def get_mp_public_key():
    return jsonify({"public_key": mp_public_key})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Los datos vienen en el cuerpo de la solicitud, no en los argumentos
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400

        if data.get('type') == 'payment' and data.get('action') == 'payment.updated':
            payment_id = data.get('data', {}).get('id')
            if payment_id:
                payment_info = sdk.payment().get(payment_id)
                
                if 'response' in payment_info:
                    payment_data = payment_info['response']
                    current_app.logger.info(f"Pago recibido: {payment_data}")
                    return jsonify({'status': 'success'}), 200
                else:
                    current_app.logger.error(f"Error al obtener información del pago: {payment_info}")
                    return jsonify({'error': 'Error al procesar el pago'}), 400
        
        return jsonify({'status': 'ignored'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error en webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        # Verificar que los datos son JSON válidos
        if not request.is_json:
            return jsonify({"error": "Se requiere JSON"}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({"error": "JSON inválido"}), 400
            
        form_id = data.get('form_id')
        if not form_id:
            return jsonify({"error": "Se requiere form_id"}), 400
            
        # Cargar datos del formulario
        json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
        if not os.path.exists(json_path):
            return jsonify({"error": "No se encontraron los datos del formulario"}), 400
            
        with open(json_path, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)

        # Generar PDF
        pdf = generate_pdf_content(cv_data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf.output(tmp_file.name)
            
            # Leer el archivo
            with open(tmp_file.name, 'rb') as f:
                pdf_bytes = f.read()
                
            # Eliminar archivo temporal
            os.unlink(tmp_file.name)
            
            # Limpiar el archivo JSON temporal
            try:
                os.remove(json_path)
            except Exception as e:
                current_app.logger.error(f"Error al eliminar archivo temporal JSON: {str(e)}")
            
            # Enviar respuesta
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=cv.pdf'
            return response
            
    except Exception as e:
        current_app.logger.error(f"Error generando PDF: {str(e)}")
        return jsonify({"error": f"Error al generar el PDF: {str(e)}"}), 500

def generate_pdf_content(data):
    try:
        app.logger.info("[DEBUG] Iniciando generación de contenido PDF")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Datos personales
        app.logger.info("[DEBUG] Procesando datos personales")
        nombre = data.get('nombre', '').strip()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=nombre or "Sin Nombre", ln=True, align='C')
        
        # Información de contacto
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Email: {data.get('email', '')}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Teléfono: {data.get('telefono', '')}", ln=True, align='L')
        pdf.cell(200, 10, txt=f"Dirección: {data.get('direccion', '')}", ln=True, align='L')
        
        # Experiencia Laboral
        app.logger.info("[DEBUG] Procesando experiencia laboral")
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Experiencia Laboral", ln=True, align='L')
        
        experiencias = data.get('experiencia', [])
        app.logger.info(f"[DEBUG] Número de experiencias: {len(experiencias)}")
        
        for exp in experiencias:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=exp.get('empresa', ''), ln=True, align='L')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Cargo: {exp.get('cargo', '')}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Periodo: {exp.get('periodo', '')}", ln=True, align='L')
            if exp.get('descripcion'):
                pdf.multi_cell(0, 10, txt=f"Descripción: {exp.get('descripcion', '')}")
            pdf.cell(200, 5, txt="", ln=True, align='L')  # Espacio
        
        # Educación
        app.logger.info("[DEBUG] Procesando educación")
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Educación", ln=True, align='L')
        
        educacion = data.get('educacion', [])
        app.logger.info(f"[DEBUG] Número de registros educativos: {len(educacion)}")
        
        for edu in educacion:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=edu.get('titulo', ''), ln=True, align='L')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Institución: {edu.get('institucion', '')}", ln=True, align='L')
            pdf.cell(200, 10, txt=f"Año: {edu.get('año', '')}", ln=True, align='L')
            pdf.cell(200, 5, txt="", ln=True, align='L')  # Espacio
        
        # Habilidades
        if data.get('habilidades'):
            app.logger.info("[DEBUG] Procesando habilidades")
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Habilidades", ln=True, align='L')
            pdf.set_font("Arial", size=12)
            habilidades = ", ".join(data.get('habilidades', []))
            pdf.multi_cell(0, 10, txt=habilidades)
        
        app.logger.info("[DEBUG] PDF generado exitosamente")
        return pdf
        
    except Exception as e:
        app.logger.error(f"[ERROR] Error en generate_pdf_content: {str(e)}")
        raise

def generate_pdf(data):
    try:
        # Generar PDF
        pdf = generate_pdf_content(data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf.output(tmp_file.name)
            
            # Leer el archivo y devolverlo como respuesta
            with open(tmp_file.name, 'rb') as f:
                pdf_bytes = f.read()
            
            # Eliminar archivo temporal
            os.unlink(tmp_file.name)
            
            return BytesIO(pdf_bytes)
            
    except Exception as e:
        current_app.logger.error(f"Error generando PDF: {str(e)}")
        raise

if __name__ == '__main__':
    # En desarrollo
    app.run(host='0.0.0.0', port=5000)
else:
    # En producción (Vercel)
    application = app
