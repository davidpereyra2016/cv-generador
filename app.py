from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response
import mercadopago
import os
from dotenv import load_dotenv
from datetime import datetime
import base64
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Estilo personalizado para el nombre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )

    # Agregar nombre
    story.append(Paragraph(cv_data['nombre'], title_style))
    story.append(Spacer(1, 12))

    # Agregar información de contacto
    contact_info = f"Email: {cv_data['email']}<br/>Teléfono: {cv_data['telefono']}"
    story.append(Paragraph(contact_info, styles['Normal']))
    story.append(Spacer(1, 12))

    # Agregar experiencia laboral
    story.append(Paragraph('Experiencia Laboral', styles['Heading2']))
    for exp in cv_data.get('experiencia', []):
        exp_text = f"{exp['empresa']} - {exp['cargo']}<br/>{exp['periodo']}<br/>{exp['descripcion']}"
        story.append(Paragraph(exp_text, styles['Normal']))
        story.append(Spacer(1, 12))

    # Agregar educación
    story.append(Paragraph('Educación', styles['Heading2']))
    for edu in cv_data.get('educacion', []):
        edu_text = f"{edu['institucion']} - {edu['titulo']}<br/>{edu['periodo']}"
        story.append(Paragraph(edu_text, styles['Normal']))
        story.append(Spacer(1, 12))

    # Agregar habilidades
    if cv_data.get('habilidades'):
        story.append(Paragraph('Habilidades', styles['Heading2']))
        skills_text = '<br/>'.join([f"• {skill}" for skill in cv_data['habilidades']])
        story.append(Paragraph(skills_text, styles['Normal']))

    doc.build(story)
    return buffer.getvalue()

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
