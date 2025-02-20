from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response
import mercadopago
import os
from dotenv import load_dotenv
from datetime import datetime
import base64
from io import BytesIO
from fpdf import FPDF

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Crear directorios necesarios
os.makedirs('bd_pdf', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Configuración de MercadoPago
mp_access_token = os.getenv('MP_ACCESS_TOKEN')
if not mp_access_token:
    raise ValueError("MP_ACCESS_TOKEN no está configurado en las variables de entorno")

sdk = mercadopago.SDK(mp_access_token)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_preference', methods=['POST'])
def create_preference():
    try:
        preference_data = {
            "items": [
                {
                    "title": "Generador de CV",
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
            "auto_return": "approved"
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        return jsonify({"id": preference["id"]})
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

def generate_pdf_content(cv_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Configuración de fuentes
    pdf.set_font('Arial', 'B', 24)
    
    # Nombre
    pdf.cell(0, 20, cv_data['nombre'], ln=True, align='C')
    
    # Información de contacto
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Email: {cv_data['email']}", ln=True)
    pdf.cell(0, 10, f"Teléfono: {cv_data['telefono']}", ln=True)
    pdf.ln(10)
    
    # Experiencia laboral
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Experiencia Laboral', ln=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    for exp in cv_data.get('experiencia', []):
        pdf.cell(0, 10, f"{exp['empresa']} - {exp['cargo']}", ln=True)
        pdf.cell(0, 10, exp['periodo'], ln=True)
        pdf.multi_cell(0, 10, exp['descripcion'])
        pdf.ln(5)
    
    # Educación
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Educación', ln=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    for edu in cv_data.get('educacion', []):
        pdf.cell(0, 10, f"{edu['institucion']} - {edu['titulo']}", ln=True)
        pdf.cell(0, 10, edu['periodo'], ln=True)
        pdf.ln(5)
    
    # Habilidades
    if cv_data.get('habilidades'):
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Habilidades', ln=True)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 12)
        for skill in cv_data['habilidades']:
            pdf.cell(0, 10, f"• {skill}", ln=True)
    
    return pdf.output(dest='S')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        cv_data = data.get('cv_data')

        if not cv_data:
            return jsonify({'error': 'Datos incompletos'}), 400

        # Generar PDF
        pdf_content = generate_pdf_content(cv_data)

        # Crear respuesta con el PDF
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=cv_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response

    except Exception as e:
        app.logger.error(f"Error generando PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
