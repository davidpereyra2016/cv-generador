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
    app.config['ENVIRONMENT'] = 'development'
else:
    # En Vercel (producción)
    UPLOAD_FOLDER = tempfile.gettempdir()
    PDF_FOLDER = tempfile.gettempdir()
    app.config['ENVIRONMENT'] = 'production'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de precios según entorno
if app.config['ENVIRONMENT'] == 'production':
    # En producción (rama main)
    PRECIO_BASICO = 1500
    PRECIO_PROFESIONAL = 2000
else:
    # En desarrollo (ramas develop, feature, etc.)
    PRECIO_BASICO = 5
    PRECIO_PROFESIONAL = 10

app.config['PRECIO_BASICO'] = PRECIO_BASICO
app.config['PRECIO_PROFESIONAL'] = PRECIO_PROFESIONAL

# Configuración de MercadoPago
mp_access_token = os.getenv('MP_ACCESS_TOKEN')
mp_public_key = os.getenv('MP_PUBLIC_KEY')

if not mp_access_token or not mp_public_key:
    raise ValueError("MP_ACCESS_TOKEN y MP_PUBLIC_KEY deben estar configurados en las variables de entorno")

sdk = mercadopago.SDK(mp_access_token)

@app.route('/')
def index():
    return render_template('index.html', 
                          precio_basico=app.config['PRECIO_BASICO'],
                          precio_profesional=app.config['PRECIO_PROFESIONAL'])

@app.route('/create_preference', methods=['POST'])
def create_preference():
    try:
        data = request.get_json()
        
        template_type = data.get("template_type", "basico")
        template_color = data.get("template_color", "azul-marino")
        external_reference = data.get("external_reference")
        
        if template_type == "profesional":
            price = app.config['PRECIO_PROFESIONAL']
        else:
            price = app.config['PRECIO_BASICO']
        
        # Cargar los datos existentes del formulario
        json_path = os.path.join(PDF_FOLDER, f'form_{external_reference}.json')
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                form_data = json.load(f)
                # Actualizar el color en los datos guardados
                form_data['template_color'] = template_color
                app.logger.info(f"[DEBUG] Actualizando color en datos guardados: {template_color}")
            
            # Guardar los datos actualizados
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(form_data, f, ensure_ascii=False, indent=2)
                app.logger.info(f"[DEBUG] Datos actualizados guardados con color: {template_color}")
        
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
        if not request.is_json:
            return jsonify({"error": "Se requiere JSON"}), 400
            
        data = request.get_json()
        
        # Verificar el color de la plantilla
        template_type = data.get('template_type')
        template_color = data.get('template_color')
        
        app.logger.info(f"[DEBUG] Tipo de plantilla recibido: {template_type}")
        app.logger.info(f"[DEBUG] Color de plantilla recibido: {template_color}")
        
        # Generar un ID único para el formulario
        form_id = str(uuid.uuid4())
        
        # Guardar los datos en un archivo JSON
        json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
        
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        app.logger.info(f"[DEBUG] Guardando datos en: {json_path}")
        app.logger.info(f"[DEBUG] Datos a guardar: {str(data)[:100]}...")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        app.logger.info(f"[DEBUG] Datos guardados exitosamente con color: {data.get('template_color')}")
        
        return jsonify({"form_id": form_id})
        
    except Exception as e:
        app.logger.error(f"[ERROR] Error al guardar datos del formulario: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/success')
def success():
    try:
        # Obtener parámetros de la URL
        payment_id = request.args.get('payment_id')
        status = request.args.get('status')
        external_reference = request.args.get('external_reference')  # Mercado Pago devuelve el form_id aquí
        
        if status != 'approved':
            return redirect(url_for('failure'))
            
        # Registrar información del pago
        if payment_id:
            try:
                payment_info = sdk.payment().get(payment_id)
                if 'response' in payment_info:
                    current_app.logger.info(f"Pago confirmado: {payment_info['response']}")
                    
                    # Obtener el form_id del external_reference o del payment_info
                    form_id = external_reference or payment_info['response'].get('external_reference')
                    
                    if form_id:
                        # Verificar que existe el archivo JSON
                        json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
                        if os.path.exists(json_path):
                            current_app.logger.info(f"[DEBUG] Archivo de datos encontrado: {json_path}")
                            with open(json_path, 'r', encoding='utf-8') as f:
                                form_data = json.load(f)
                            
                            # Obtener el color de la plantilla
                            template_type = form_data.get('template_type', 'basico')
                            template_color = form_data.get('template_color', 'azul-marino')
                            
                            current_app.logger.info(f"[DEBUG] Tipo de plantilla: {template_type}")
                            current_app.logger.info(f"[DEBUG] Color de plantilla: {template_color}")
                            
                            # Renderizar success.html con el form_id y template_color
                            return render_template('success.html',
                                               template_type=template_type,
                                               template_color=template_color,
                                               payment_id=payment_id,
                                               form_id=form_id)
                        else:
                            current_app.logger.error(f"[ERROR] No se encontró el archivo de datos: {json_path}")
                    else:
                        current_app.logger.error("[ERROR] No se encontró form_id en la respuesta del pago")
            except Exception as e:
                current_app.logger.error(f"[ERROR] Error al verificar pago: {str(e)}")
        
        # Si no se encuentra el form_id o hay algún error, mostrar mensaje de error
        return render_template('error.html',
                           message="No se pudieron recuperar los datos del CV. Por favor, intente nuevamente.")
        
    except Exception as e:
        current_app.logger.error(f"[ERROR] Error en success: {str(e)}")
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
        app.logger.info(f"[DEBUG] Color recibido: {data.get('template_color', 'No especificado')}")
        
        # Guardar la imagen y el color si están presentes en los datos directos
        profile_image = data.get('profile_image')
        template_color = data.get('template_color')
        
        # Si se proporciona form_id, cargar datos del archivo JSON
        if 'form_id' in data:
            form_id = data['form_id']
            json_path = os.path.join(PDF_FOLDER, f'form_{form_id}.json')
            
            if os.path.exists(json_path):
                app.logger.info(f"[DEBUG] Cargando datos del archivo: {json_path}")
                with open(json_path, 'r', encoding='utf-8') as f:
                    stored_data = json.load(f)
                    
                # Mantener la imagen del perfil si se proporcionó en los datos directos
                if profile_image:
                    stored_data['profile_image'] = profile_image
                    app.logger.info("[DEBUG] Usando imagen proporcionada en los datos directos")
                elif 'profile_image' in stored_data:
                    app.logger.info("[DEBUG] Usando imagen del archivo JSON almacenado")
                else:
                    app.logger.warning("[WARNING] No se encontró imagen ni en los datos directos ni en el archivo JSON")
                
                # Mantener el color si se proporcionó en los datos directos
                if template_color:
                    stored_data['template_color'] = template_color
                    app.logger.info(f"[DEBUG] Usando color proporcionado en los datos directos: {template_color}")
                elif 'template_color' in stored_data:
                    app.logger.info(f"[DEBUG] Usando color del archivo JSON almacenado: {stored_data['template_color']}")
                else:
                    app.logger.warning("[WARNING] No se encontró color ni en los datos directos ni en el archivo JSON")
                
                # Actualizar otros campos desde los datos directos
                stored_data['template_type'] = data.get('template_type', stored_data.get('template_type', 'basico'))
                
                data = stored_data
            else:
                app.logger.error(f"[ERROR] No se encontró el archivo: {json_path}")
                return jsonify({"error": "Datos no encontrados"}), 404
        
        # Aplicar capitalize a los campos necesarios
        nombre = capitalize_text(data.get('nombre', ''))
        
        experiencia = data.get('experiencia', [])
        for exp in experiencia:
            exp['empresa'] = capitalize_text(exp.get('empresa', ''))
            exp['cargo'] = capitalize_text(exp.get('cargo', ''))
            
        educacion = data.get('educacion', [])
        for edu in educacion:
            edu['titulo'] = capitalize_text(edu.get('titulo', ''))
            edu['institucion'] = capitalize_text(edu.get('institucion', ''))
        
        # Verificar si hay imagen después de todo el proceso
        if 'profile_image' in data:
            app.logger.info(f"[DEBUG] Imagen encontrada en los datos finales, longitud: {len(data['profile_image'])}")
        else:
            app.logger.warning("[WARNING] No se encontró imagen en los datos finales")
            
        # Verificar el color final
        app.logger.info(f"[DEBUG] Color final a usar: {data.get('template_color', 'No especificado')}")
        
        # Generar PDF con el contenido requerido
        try:
            # Generar el PDF
            pdf = generate_pdf_content(data)
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                # Guardar el PDF en el archivo temporal
                pdf.output(tmp_file.name)
                tmp_file_path = tmp_file.name
                app.logger.info(f"[DEBUG] PDF generado y guardado en: {tmp_file_path}")
                
                # Leer el archivo generado
                with open(tmp_file_path, 'rb') as f:
                    pdf_bytes = f.read()
                    app.logger.info(f"[DEBUG] PDF leído correctamente, tamaño: {len(pdf_bytes)} bytes")
                
                # Eliminar archivo temporal
                try:
                    os.unlink(tmp_file_path)
                    app.logger.info(f"[DEBUG] Archivo temporal eliminado: {tmp_file_path}")
                except Exception as e:
                    app.logger.error(f"[ERROR] Error al eliminar archivo temporal: {str(e)}")
                
                # Crear y enviar la respuesta
                response = make_response(pdf_bytes)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'attachment; filename=cv.pdf'
                app.logger.info("[INFO] PDF enviado correctamente al cliente")
                return response
        except Exception as e:
            app.logger.error(f"[ERROR] Error durante la generación o entrega del PDF: {str(e)}")
            raise
            
    except Exception as e:
        app.logger.error(f"[ERROR] Error generando PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

def capitalize_text(text):
    """Capitaliza cada palabra en el texto."""
    if text:
        return ' '.join(word.capitalize() for word in text.split())
    return ''

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
        
        # Obtener color seleccionado (solo para plantilla profesional)
        template_color = data.get('template_color', 'azul-marino')
        
        # Configuración de colores según la plantilla y el color seleccionado
        if template_type == 'profesional':
            if template_color == 'azul-marino':
                header_color = (26, 73, 113)  # #1a4971 - Azul marino
                text_color = (68, 68, 68)  # #444444
                accent_color = (26, 73, 113)  # #1a4971
            elif template_color == 'amarillo-claro':
                header_color = (242, 201, 76)  # #F2C94C - Amarillo claro
                text_color = (68, 68, 68)  # #444444
                accent_color = (242, 201, 76)  # #F2C94C
            elif template_color == 'rosado-pastel':
                header_color = (242, 166, 166)  # #F2A6A6 - Rosado pastel
                text_color = (68, 68, 68)  # #444444
                accent_color = (242, 166, 166)  # #F2A6A6
            elif template_color == 'morado':
                header_color = (149, 91, 165)  # #955BA5 - Morado
                text_color = (68, 68, 68)  # #444444
                accent_color = (149, 91, 165)  # #955BA5
            else:
                # Valor por defecto (azul marino)
                header_color = (26, 73, 113)  # #1a4971
                text_color = (68, 68, 68)  # #444444
                accent_color = (26, 73, 113)  # #1a4971
        else:
            header_color = (100, 100, 100)  # Cambiado de #4a4a4a a un gris más claro
            text_color = (0, 0, 0)  # #000000
            accent_color = (74, 74, 74)  # #4a4a4a
        
        # Encabezado con datos personales
        pdf.set_fill_color(*header_color)
        pdf.rect(0, 0, 210, 40, 'F')  # Reducimos la altura del encabezado de 50 a 40
        
        # Si es plantilla profesional y hay imagen, agregarla
        if template_type == 'profesional' and data.get('profile_image'):
            try:
                # Importar PIL para manejar las imágenes
                from PIL import Image
                import io
                
                # Decodificar la imagen base64
                image_data = data['profile_image']
                app.logger.info(f"[DEBUG] Imagen recibida (longitud): {len(image_data)}")
                app.logger.info(f"[DEBUG] Primeros 50 caracteres de la imagen: {image_data[:50]}...")
                
                # Asegurarse de que la cadena base64 esté correctamente formateada
                if ',' in image_data:
                    app.logger.info(f"[DEBUG] Encontrado separador en la imagen base64")
                    image_data = image_data.split(',')[1]
                
                # Decodificar la imagen
                try:
                    image_bytes = base64.b64decode(image_data)
                    app.logger.info(f"[DEBUG] Imagen decodificada correctamente, tamaño: {len(image_bytes)} bytes")
                    
                    # Crear un objeto de imagen con PIL
                    img = Image.open(io.BytesIO(image_bytes))
                    app.logger.info(f"[DEBUG] Imagen abierta con PIL: formato={img.format}, tamaño={img.size}")
                    
                    # Redimensionar la imagen si es necesario
                    max_size = (300, 300)
                    if img.width > max_size[0] or img.height > max_size[1]:
                        img.thumbnail(max_size, Image.LANCZOS)
                        app.logger.info(f"[DEBUG] Imagen redimensionada a {img.size}")
                    
                    # Convertir a RGB si tiene transparencia (modo RGBA)
                    if img.mode == 'RGBA':
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[3])  # Usar el canal alfa como máscara
                        img = rgb_img
                        app.logger.info("[DEBUG] Imagen convertida de RGBA a RGB")
                    
                    # Guardar como JPEG en un archivo temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_img:
                        img.save(temp_img.name, 'JPEG', quality=95)
                        temp_img_path = temp_img.name
                        app.logger.info(f"[DEBUG] Imagen guardada como JPEG en: {temp_img_path}")
                    
                    # Agregar imagen al PDF - usar 'jpg' en minúsculas para FPDF 1.7.2
                    try:
                        pdf.image(temp_img_path, x=170, y=5, w=30, h=30, type='jpg')
                        app.logger.info("[DEBUG] Imagen agregada al PDF correctamente")
                    except Exception as e:
                        app.logger.error(f"[ERROR] Error al agregar la imagen al PDF: {str(e)}")
                        app.logger.error(f"[ERROR] Ruta de la imagen: {temp_img_path}")
                        app.logger.error(f"[ERROR] ¿Existe el archivo?: {os.path.exists(temp_img_path)}")
                        raise
                    
                    # Eliminar archivo temporal
                    try:
                        os.unlink(temp_img_path)
                        app.logger.info("[DEBUG] Archivo temporal de imagen eliminado")
                    except Exception as e:
                        app.logger.error(f"[ERROR] Error al eliminar archivo temporal: {str(e)}")
                except Exception as e:
                    app.logger.error(f"[ERROR] Error al procesar la imagen con PIL: {str(e)}")
                    raise
            except Exception as e:
                app.logger.error(f"[ERROR] Error al procesar la imagen: {str(e)}")
                app.logger.error(f"[ERROR] Tipo de datos de la imagen: {type(data.get('profile_image'))}")
                # Continuar sin la imagen en caso de error
                app.logger.info("[INFO] Continuando la generación del PDF sin la imagen debido al error")
        
        # Nombre
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(255, 255, 255)  # Blanco
        pdf.set_xy(10, 10)
        pdf.cell(160, 10, txt=capitalize_text(data.get('nombre', 'Sin Nombre')), ln=True, align='L')
        
        # Información de contacto secundaria (uno debajo del otro)
        pdf.set_font("Arial", '', 11)
        pdf.set_xy(10, 25)  # Reducido de 30 a 25
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
        pdf.ln(5)  # Reducido de 20 a 5 para disminuir el espacio
        
        # Experiencia Laboral
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*accent_color)
        pdf.cell(0, 10, txt="Experiencia Laboral", ln=True, align='L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        experiencia = data.get('experiencia', [])
        for exp in experiencia:
            # Empresa y periodo en la misma línea
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(*accent_color)
            empresa = exp.get('empresa', '')
            periodo = exp.get('periodo', '')
            
            # Calcular ancho del texto de la empresa
            empresa_width = pdf.get_string_width(empresa)
            
            # Imprimir empresa
            pdf.cell(empresa_width + 5, 8, txt=capitalize_text(empresa), align='L')
            
            # Imprimir periodo a la derecha
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 8, txt=periodo, ln=True, align='R')
            
            # Cargo
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 6, txt=capitalize_text(exp.get('cargo', '')), ln=True, align='L')
            
            # Descripción
            if exp.get('descripcion'):
                pdf.set_font("Arial", '', 10)
                pdf.multi_cell(0, 6, txt=exp.get('descripcion', ''))
            
            pdf.ln(3)  # Reducido de 5 a 3
        
        # Educación
        pdf.ln(2)  # Reducido de 5 a 2
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*accent_color)
        pdf.cell(0, 10, txt="Educación", ln=True, align='L')
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
            pdf.cell(titulo_width + 5, 8, txt=capitalize_text(titulo), align='L')
            
            # Imprimir año a la derecha
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 8, txt=anio, ln=True, align='R')
            
            # Institución
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(*text_color)
            pdf.cell(0, 6, txt=capitalize_text(edu.get('institucion', '')), ln=True, align='L')
            
            pdf.ln(3)  # Reducido de 5 a 3
        
        # Habilidades
        pdf.ln(2)  # Reducido de 5 a 2
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(*accent_color)
        pdf.cell(0, 10, txt="Habilidades", ln=True, align='L')
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
        app.logger.info("[DEBUG] Iniciando generate_pdf")
        
        # Generar PDF
        pdf = generate_pdf_content(data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            app.logger.info(f"[DEBUG] Generando PDF en archivo temporal: {tmp_file.name}")
            pdf.output(tmp_file.name)
            tmp_path = tmp_file.name
            
        # Leer el archivo y devolverlo como respuesta
        app.logger.info(f"[DEBUG] Leyendo archivo PDF generado: {tmp_path}")
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
            app.logger.info(f"[DEBUG] PDF leído, tamaño: {len(pdf_bytes)} bytes")
        
        # Eliminar archivo temporal
        try:
            os.unlink(tmp_path)
            app.logger.info(f"[DEBUG] Archivo temporal eliminado: {tmp_path}")
        except Exception as e:
            app.logger.error(f"[ERROR] Error al eliminar archivo temporal: {str(e)}")
        
        # Crear BytesIO para manejar el PDF en memoria
        pdf_buffer = BytesIO(pdf_bytes)
        app.logger.info("[DEBUG] PDF convertido a BytesIO")
        return pdf_buffer
    except Exception as e:
        app.logger.error(f"[ERROR] Error en generate_pdf: {str(e)}")
        raise

if __name__ == '__main__':
    # En desarrollo
    app.run(host='0.0.0.0', port=5000)
else:
    # En producción (Vercel)
    application = app
