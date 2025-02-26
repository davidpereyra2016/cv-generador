from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, make_response, current_app
import mercadopago
import os
import json
import tempfile
import base64
from dotenv import load_dotenv
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import uuid

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import io

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
            price = 10
        else:
            price = 5
        
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
                    
                    # Si no hay form_id o no se encuentra el archivo, usar localStorage como respaldo
                    return render_template('success.html',
                                        template_type=request.args.get('template_type', 'basico'),
                                        payment_id=payment_id,
                                        use_localstorage=True)
            except Exception as e:
                current_app.logger.error(f"Error al verificar pago: {str(e)}")
        
        return render_template('success.html',
                            template_type=request.args.get('template_type', 'basico'),
                            payment_id=payment_id,
                            use_localstorage=True)
        
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
            
        # Obtener datos del CV, ya sea del archivo JSON o directamente
        cv_data = None
        
        if 'cv_data' in data:
            cv_data = data['cv_data']
        elif 'form_id' in data:
            json_path = os.path.join(PDF_FOLDER, f'form_{data["form_id"]}.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    cv_data = json.load(f)
                try:
                    os.remove(json_path)
                except Exception as e:
                    current_app.logger.error(f"Error al eliminar archivo temporal: {str(e)}")
        
        if cv_data is None:
            return jsonify({"error": "No se encontraron datos del CV"}), 400

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
            
            # Enviar respuesta
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=cv.pdf'
            return response
            
    except Exception as e:
        current_app.logger.error(f"Error generando PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    try:
        # Verificar que los datos son JSON válidos
        if not request.is_json:
            app.logger.error("[ERROR] La solicitud no contiene JSON")
            return jsonify({"error": "Se requiere JSON"}), 400
            
        data = request.get_json()
        if data is None:
            app.logger.error("[ERROR] JSON inválido")
            return jsonify({"error": "JSON inválido"}), 400
        
        app.logger.info(f"[DEBUG] Datos recibidos para PDF: {str(data)[:100]}...")
        
        # Verificar si hay imagen
        if 'profile_image' in data:
            app.logger.info(f"[DEBUG] Imagen encontrada en los datos, longitud: {len(data['profile_image'])}")
        else:
            app.logger.warning("[WARNING] No se encontró imagen en los datos")
        
        # Generar PDF
        pdf = generate_pdf_content(data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf.output(tmp_file.name)
            
            # Leer el archivo
            with open(tmp_file.name, 'rb') as f:
                pdf_bytes = f.read()
                
            # Eliminar archivo temporal
            os.unlink(tmp_file.name)
            
            # Enviar respuesta
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=cv.pdf'
            return response
            
    except Exception as e:
        app.logger.error(f"[ERROR] Error generando PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

def generate_pdf_content(data):
    try:
        app.logger.info("[DEBUG] Iniciando generación de contenido PDF")
        app.logger.info(f"[DEBUG] Tipo de plantilla: {data.get('template_type', 'No especificado')}")
        app.logger.info(f"[DEBUG] ¿Tiene imagen?: {'Sí' if data.get('profile_image') else 'No'}")
        
        # Importar módulos necesarios
        import base64
        import tempfile
        import os
        import re
        
        pdf = FPDF()
        pdf.add_page()
        
        # Determinar tipo de plantilla
        template_type = data.get('template_type', 'basico')
        
        # Configuración de colores
        if template_type == 'profesional':
            header_color = (26, 73, 113)  # #1a4971
            text_color = (68, 68, 68)  # #444444
            accent_color = (26, 73, 113)  # #1a4971
        else:
            header_color = (100, 100, 100)  # Cambiado de #4a4a4a a un gris más claro
            text_color = (0, 0, 0)  # #000000
            accent_color = (74, 74, 74)  # #4a4a4a
            
        # Encabezado con datos personales
        pdf.set_fill_color(*header_color)
        pdf.rect(0, 0, 210, 50, 'F')  # Aumentamos la altura del encabezado
        
        # Si es plantilla profesional y hay imagen, agregarla
        if template_type == 'profesional' and data.get('profile_image'):
            try:
                # Decodificar la imagen base64
                image_data = data['profile_image']
                app.logger.info(f"[DEBUG] Imagen recibida (longitud): {len(image_data)}")
                app.logger.info(f"[DEBUG] Primeros 50 caracteres de la imagen: {image_data[:50]}...")
                
                # Determinar el formato de la imagen
                image_format = 'JPEG'  # Formato predeterminado
                if 'data:image/' in image_data:
                    # Extraer el formato de la cadena data URL
                    format_match = re.search(r'data:image/(\w+);base64,', image_data)
                    if format_match:
                        detected_format = format_match.group(1).upper()
                        app.logger.info(f"[DEBUG] Formato de imagen detectado: {detected_format}")
                        if detected_format in ['JPEG', 'JPG', 'PNG', 'GIF']:
                            image_format = 'JPEG' if detected_format in ['JPEG', 'JPG'] else detected_format
                
                # Asegurarse de que la cadena base64 esté correctamente formateada
                if ',' in image_data:
                    app.logger.info(f"[DEBUG] Encontrado separador en la imagen base64")
                    image_data = image_data.split(',')[1]
                
                # Decodificar la imagen
                try:
                    image_bytes = base64.b64decode(image_data)
                    app.logger.info(f"[DEBUG] Imagen decodificada correctamente, tamaño: {len(image_bytes)} bytes")
                except Exception as e:
                    app.logger.error(f"[ERROR] Error al decodificar la imagen: {str(e)}")
                    app.logger.error(f"[ERROR] Primeros 50 caracteres de la imagen: {image_data[:50]}...")
                    raise
                
                # Guardar temporalmente la imagen con la extensión correcta
                extension = '.jpg' if image_format == 'JPEG' else f'.{image_format.lower()}'
                
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_img:
                        temp_img.write(image_bytes)
                        temp_img.flush()
                        temp_img_path = temp_img.name
                        app.logger.info(f"[DEBUG] Imagen guardada temporalmente en: {temp_img_path} con formato {image_format}")
                except Exception as e:
                    app.logger.error(f"[ERROR] Error al guardar la imagen temporal: {str(e)}")
                    raise
                
                # Agregar imagen al PDF
                try:
                    # Usar coordenadas específicas para la plantilla profesional
                    pdf.image(temp_img_path, x=170, y=5, w=30, h=30, type=image_format)
                    app.logger.info(f"[DEBUG] Imagen agregada al PDF correctamente con formato {image_format}")
                except Exception as e:
                    app.logger.error(f"[ERROR] Error al agregar la imagen al PDF: {str(e)}")
                    app.logger.error(f"[ERROR] Ruta de la imagen: {temp_img_path}")
                    app.logger.error(f"[ERROR] ¿Existe el archivo?: {os.path.exists(temp_img_path)}")
                    app.logger.error(f"[ERROR] Tamaño del archivo: {os.path.getsize(temp_img_path) if os.path.exists(temp_img_path) else 'No existe'}")
                    app.logger.error(f"[ERROR] Intentando con otro método...")
                    
                    # Intentar con diferentes formatos si el primero falla
                    for alt_format in ['JPEG', 'PNG', 'GIF']:
                        if alt_format != image_format:
                            try:
                                app.logger.info(f"[DEBUG] Intentando con formato alternativo: {alt_format}")
                                pdf.image(temp_img_path, x=170, y=5, w=30, h=30, type=alt_format)
                                app.logger.info(f"[DEBUG] Imagen agregada al PDF correctamente con formato alternativo {alt_format}")
                                break
                            except Exception as e2:
                                app.logger.error(f"[ERROR] Error con formato alternativo {alt_format}: {str(e2)}")
                finally:
                    # Eliminar archivo temporal
                    try:
                        os.unlink(temp_img_path)
                        app.logger.info("[DEBUG] Archivo temporal de imagen eliminado")
                    except Exception as e:
                        app.logger.error(f"[ERROR] Error al eliminar archivo temporal: {str(e)}")
            except Exception as e:
                app.logger.error(f"[ERROR] Error al procesar la imagen: {str(e)}")
                app.logger.error(f"[ERROR] Tipo de datos de la imagen: {type(data.get('profile_image'))}")
                # Continuar sin la imagen en caso de error
                app.logger.info("[INFO] Continuando la generación del PDF sin la imagen debido al error")
        
        # Nombre
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(255, 255, 255)  # Blanco
        pdf.set_xy(10, 10)
        pdf.cell(160, 10, txt=data.get('nombre', 'Sin Nombre'), ln=True, align='L')
        
        # Información de contacto secundaria (uno debajo del otro)
        pdf.set_font("Arial", '', 11)
        pdf.set_xy(10, 30)
        if data.get('dni'):
            pdf.cell(160, 5, txt=f"DNI: {data.get('dni')}", ln=True, align='L')
        if data.get('fecha_nacimiento'):
            pdf.cell(160, 5, txt=f"Fecha de Nacimiento: {data.get('fecha_nacimiento')}", ln=True, align='L')
        if data.get('edad'):
            pdf.cell(160, 5, txt=f"Edad: {data.get('edad')}", ln=True, align='L')
        
        # Información de contacto primaria (en línea) debajo de la información secundaria
        current_y = pdf.get_y()
        pdf.set_xy(10, current_y)
        contact_primary = []
        if data.get('email'): contact_primary.append(f"Email: {data.get('email')}")
        if data.get('telefono'): contact_primary.append(f"Tel: {data.get('telefono')}")
        if data.get('direccion'): contact_primary.append(f"Dirección: {data.get('direccion')}")
        pdf.cell(160, 6, txt=" | ".join(contact_primary), ln=True, align='L')
        
        # Resetear color de texto y continuar con el resto del CV
        pdf.set_text_color(*text_color)
        pdf.ln(20)
        
        # Experiencia Laboral
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*accent_color)
        pdf.cell(0, 10, txt="EXPERIENCIA LABORAL", ln=True, align='L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        experiencias = data.get('experiencia', [])
        for exp in experiencias:
            # Empresa y periodo en la misma línea
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(*accent_color)
            empresa = exp.get('empresa', '')
            periodo = exp.get('periodo', '')
            
            # Calcular ancho del texto de la empresa
            empresa_width = pdf.get_string_width(empresa)
            
            # Imprimir empresa
            pdf.cell(empresa_width + 5, 8, txt=empresa, align='L')
            
            # Imprimir periodo a la derecha
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 8, txt=periodo, ln=True, align='R')
            
            # Cargo
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 6, txt=exp.get('cargo', ''), ln=True, align='L')
            
            # Descripción
            if exp.get('descripcion'):
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, txt=exp.get('descripcion', ''))
            
            pdf.ln(5)
        
        # Educación
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*accent_color)
        pdf.cell(0, 10, txt="EDUCACIÓN", ln=True, align='L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        educacion = data.get('educacion', [])
        for edu in educacion:
            # Título y año en la misma línea
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(*accent_color)
            titulo = edu.get('titulo', '')
            anio = edu.get('año', '')
            
            # Calcular ancho del texto del título
            titulo_width = pdf.get_string_width(titulo)
            
            # Imprimir título
            pdf.cell(titulo_width + 5, 8, txt=titulo, align='L')
            
            # Imprimir año a la derecha
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 8, txt=anio, ln=True, align='R')
            
            # Institución
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 6, txt=edu.get('institucion', ''), ln=True, align='L')
            
            pdf.ln(5)
        
        # Habilidades
        if data.get('habilidades'):
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 16)
            pdf.set_text_color(*accent_color)
            pdf.cell(0, 10, txt="HABILIDADES", ln=True, align='L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            # Crear lista de habilidades
            pdf.set_font("Arial", '', 11)
            pdf.set_text_color(*text_color)
            for habilidad in data.get('habilidades', []):
                pdf.cell(0, 6, txt="- " + habilidad, ln=True, align='L')  # Usando guión en lugar de bullet point
        
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
