from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response
import mercadopago
import os
from dotenv import load_dotenv
from datetime import datetime
import base64
import tempfile
from xhtml2pdf import pisa
from io import BytesIO

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

def html_to_pdf(html_content):
    # Crear un buffer de memoria para el PDF
    result = BytesIO()
    
    # Convertir HTML a PDF
    pisa.CreatePDF(
        html_content,
        dest=result,
        encoding='utf-8'
    )
    
    # Obtener el contenido del buffer
    pdf_content = result.getvalue()
    result.close()
    
    return pdf_content

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        template_type = data.get('template_type')
        cv_data = data.get('cv_data')

        if not template_type or not cv_data:
            return jsonify({'error': 'Datos incompletos'}), 400

        # Seleccionar la plantilla correcta
        template = 'cv_template_basico.html' if template_type == 'basico' else 'cv_template_profesional.html'
        
        # Renderizar el HTML
        html_content = render_template(template, cv_data=cv_data)
        
        # Convertir HTML a PDF
        pdf_content = html_to_pdf(html_content)

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
