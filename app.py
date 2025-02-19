from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response
import mercadopago
import os
from dotenv import load_dotenv
import pdfkit
import json
from datetime import datetime
import base64

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Crear directorios necesarios si no existen
os.makedirs('static/img', exist_ok=True)
os.makedirs('bd_pdf', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Configuración de wkhtmltopdf
if os.name == 'nt':  # Windows
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if os.path.exists(path_wkhtmltopdf):
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    else:
        raise Exception("wkhtmltopdf no está instalado. Por favor, instálalo desde https://wkhtmltopdf.org/downloads.html")
else:  # Linux/Unix
    config = pdfkit.configuration()

# Configuración de MercadoPago
sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crear_preferencia', methods=['POST'])
def crear_preferencia():
    try:
        data = request.get_json()
        template_type = data.get('template_type', 'basico')
        
        # Definir precio según el tipo de plantilla
        precios = {
            'basico': 1000,  # 1000 pesos argentinos
            'profesional': 2000  # 2000 pesos argentinos
        }
        
        precio = precios[template_type]
        
        preference_data = {
            "items": [
                {
                    "title": f"CV {template_type.capitalize()}",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": precio
                }
            ],
            "back_urls": {
                "success": url_for('success', _external=True),
                "failure": url_for('failure', _external=True),
                "pending": url_for('pending', _external=True)
            },
            "auto_return": "approved"
        }
        
        # Crear preferencia en MercadoPago
        preference = sdk.preference().create(preference_data)
        
        return jsonify({
            "init_point": preference["response"]["init_point"],
            "template_type": template_type,
            "precio": precio
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/success')
def success():
    # Obtener el ID del pago y el estado
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    
    if status == 'approved':
        # Verificar el pago con MercadoPago
        payment_info = sdk.payment().get(payment_id)
        payment_amount = payment_info["response"]["transaction_amount"]
        
        # Determinar el tipo de plantilla según el monto pagado
        template_type = 'profesional' if payment_amount >= 2000 else 'basico'
        
        return render_template('success.html', 
                            payment_id=payment_id, 
                            status=status,
                            template_type=template_type)
    else:
        return redirect(url_for('failure'))

@app.route('/failure')
def failure():
    return render_template('failure.html')

@app.route('/pending')
def pending():
    return render_template('pending.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        template_type = data.get('template_type')
        cv_data = data.get('cv_data')

        # Asegurarse de que la carpeta bd_pdf existe
        if not os.path.exists('bd_pdf'):
            os.makedirs('bd_pdf')

        # Seleccionar la plantilla correcta
        template = 'cv_template_basico.html' if template_type == 'basico' else 'cv_template_profesional.html'
        
        # Renderizar el HTML
        html = render_template(template, cv_data=cv_data)
        
        # Generar nombre único para el PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f'cv_{timestamp}.pdf'
        pdf_path = os.path.join('bd_pdf', pdf_filename)

        # Configurar opciones de wkhtmltopdf
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None
        }

        # Generar PDF
        config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        pdfkit.from_string(html, pdf_path, options=options, configuration=config)

        # Leer el archivo PDF generado
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        # Crear respuesta con el PDF
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={pdf_filename}'
        
        return response

    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
