// Variable global para MercadoPago
let mp;

// Inicializar MercadoPago
async function initMercadoPago() {
    try {
        const response = await fetch('/get_mp_public_key');
        const data = await response.json();
        mp = new MercadoPago(data.public_key);
    } catch (error) {
        console.error('Error al inicializar MercadoPago:', error);
    }
}

// Función para manejar la carga de la imagen
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImage').src = e.target.result;
            localStorage.setItem('profile_image', e.target.result);
        };
        reader.readAsDataURL(file);
    }
}

// Actualizar vista previa en tiempo real
function updatePreview() {
    const form = document.getElementById('cvForm');
    const formData = new FormData(form);
    
    // Obtener la imagen del input file
    const fileInput = document.querySelector('input[type="file"]');
    const imagePreview = document.getElementById('imagePreview');
    if (fileInput.files && fileInput.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            localStorage.setItem('profile_image', e.target.result);
        }
        reader.readAsDataURL(fileInput.files[0]);
    }

    const cvData = {
        nombre: formData.get('nombre'),
        email: formData.get('email'),
        telefono: formData.get('telefono'),
        direccion: formData.get('direccion'),
        dni: formData.get('dni'),
        fecha_nacimiento: formData.get('fecha_nacimiento'),
        profile_image: localStorage.getItem('profile_image'),
        experiencia: [],
        educacion: [],
        habilidades: formData.getAll('habilidades[]').filter(h => h.trim())
    };

    // Procesar experiencia
    const empresas = formData.getAll('empresa[]');
    const cargos = formData.getAll('cargo[]');
    const fechasInicio = formData.getAll('fecha_inicio[]');
    const fechasFin = formData.getAll('fecha_fin[]');
    const descripciones = formData.getAll('descripcion[]');
    const trabajoActual = formData.getAll('trabajo_actual[]');

    empresas.forEach((empresa, index) => {
        if (empresa) {
            let periodo = '';
            if (fechasInicio[index]) {
                periodo = fechasInicio[index];
                if (trabajoActual[index] === 'on') {
                    periodo += ',Presente';
                } else if (fechasFin[index]) {
                    periodo += ',' + fechasFin[index];
                }
            }
            
            cvData.experiencia.push({
                empresa: empresa,
                cargo: cargos[index] || '',
                periodo: periodo,
                descripcion: descripciones[index] || ''
            });
        }
    });

    // Procesar educación
    const titulos = formData.getAll('titulo[]');
    const instituciones = formData.getAll('institucion[]');
    const fechasInicioEdu = formData.getAll('fecha_inicio_edu[]');
    const fechasFinEdu = formData.getAll('fecha_fin_edu[]');
    const enCurso = formData.getAll('en_curso[]');

    titulos.forEach((titulo, index) => {
        if (titulo) {
            let año = '';
            if (fechasInicioEdu[index]) {
                año = fechasInicioEdu[index];
                if (enCurso[index] === 'on') {
                    año += ',En curso';
                } else if (fechasFinEdu[index]) {
                    año += ',' + fechasFinEdu[index];
                }
            }
            
            cvData.educacion.push({
                titulo: titulo,
                institucion: instituciones[index] || '',
                año: año
            });
        }
    });

    // Guardar en localStorage para usar después
    localStorage.setItem('cv_data', JSON.stringify(cvData));

    // Actualizar vista previa
    const template = document.querySelector('input[name="template_type"]:checked').value;
    const previewHtml = template === 'basico' ? 
        generateBasicTemplate(cvData) : 
        generateProTemplate(cvData);
    
    document.getElementById('cvPreview').innerHTML = previewHtml;
}

function generateBasicTemplate(data) {
    return `
    <div class="cv-preview">
        <div class="header">
            ${data.profile_image ? `<img src="${data.profile_image}" alt="Foto de perfil" class="profile-image">` : ''}
            <div class="header-info">
                <h1>${data.nombre || ''}</h1>
                <div class="contact-info">
                    ${data.email ? `<p>📧 ${data.email}</p>` : ''}
                    ${data.telefono ? `<p>📱 ${data.telefono}</p>` : ''}
                    ${data.direccion ? `<p>📍 ${data.direccion}</p>` : ''}
                    ${data.dni ? `<p>🆔 DNI: ${data.dni}</p>` : ''}
                    ${data.fecha_nacimiento ? `<p>📅 ${data.fecha_nacimiento}</p>` : ''}
                </div>
            </div>
        </div>

        ${data.experiencia && data.experiencia.length ? `
            <div class="section">
                <h2>Experiencia Laboral</h2>
                ${data.experiencia.map(exp => `
                    <div class="experience-item">
                        <div class="info-principal">
                            <div class="empresa">${exp.empresa}</div>
                            <div class="cargo">${exp.cargo}</div>
                            ${exp.descripcion ? `<div class="descripcion">${exp.descripcion}</div>` : ''}
                        </div>
                        <div class="periodo">${exp.periodo}</div>
                    </div>
                `).join('')}
            </div>
        ` : ''}

        ${data.educacion && data.educacion.length ? `
            <div class="section">
                <h2>Educación</h2>
                ${data.educacion.map(edu => `
                    <div class="education-item">
                        <div class="info-principal">
                            <div class="empresa">${edu.institucion}</div>
                            <div class="cargo">${edu.titulo}</div>
                        </div>
                        <div class="periodo">${edu.año}</div>
                    </div>
                `).join('')}
            </div>
        ` : ''}

        ${data.habilidades && data.habilidades.length ? `
            <div class="section">
                <h2>Habilidades</h2>
                <div class="skills">
                    ${data.habilidades.map(skill => `
                        <span class="skill">${skill}</span>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    </div>`;
}

function generateProTemplate(data) {
    return generateBasicTemplate(data); // Usar el mismo template por ahora
}

// Agregar listeners para todos los campos del formulario
document.addEventListener('DOMContentLoaded', async function() {
    // Inicializar MercadoPago
    await initMercadoPago();
    
    updatePreview(); // Actualizar vista previa inicial
    
    // Listener para cambios en el formulario
    document.getElementById('cvForm').addEventListener('input', updatePreview);
    document.querySelectorAll('input[name="template_type"]').forEach(radio => {
        radio.addEventListener('change', updatePreview);
    });
    
    // Listener para carga de imagen
    document.getElementById('profileImageInput').addEventListener('change', handleImageUpload);
});

function agregarExperiencia() {
    const container = document.getElementById('experienciaContainer');
    const nuevaExperiencia = document.createElement('div');
    nuevaExperiencia.className = 'experiencia-item';
    nuevaExperiencia.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <label for="empresa">Empresa</label>
                <input type="text" class="form-control" name="empresa[]" placeholder="Nombre de la empresa">
            </div>
            <div class="col-md-6 mb-3">
                <label for="cargo">Cargo</label>
                <input type="text" class="form-control" name="cargo[]" placeholder="Tu cargo">
            </div>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <label for="fecha_inicio">Fecha de Inicio</label>
                <input type="date" class="form-control" name="fecha_inicio[]">
            </div>
            <div class="col-md-6 mb-3">
                <label for="fecha_fin">Fecha de Fin</label>
                <input type="date" class="form-control" name="fecha_fin[]">
                <div class="form-check mt-2">
                    <input class="form-check-input" type="checkbox" name="trabajo_actual[]">
                    <label class="form-check-label">Trabajo actual</label>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-12 mb-3">
                <label for="descripcion">Descripción</label>
                <textarea class="form-control" name="descripcion[]" rows="3" placeholder="Describe tus responsabilidades"></textarea>
            </div>
        </div>
        <button type="button" class="btn btn-danger mb-3" onclick="this.parentElement.remove()">Eliminar</button>
    `;
    container.insertBefore(nuevaExperiencia, container.lastElementChild);
}

function agregarEducacion() {
    const container = document.getElementById('educacionContainer');
    const nuevaEducacion = document.createElement('div');
    nuevaEducacion.className = 'educacion-item';
    nuevaEducacion.innerHTML = `
        <div class="row">
            <div class="col-md-6 mb-3">
                <label for="titulo">Título</label>
                <input type="text" class="form-control" name="titulo[]" placeholder="Título obtenido">
            </div>
            <div class="col-md-6 mb-3">
                <label for="institucion">Institución</label>
                <input type="text" class="form-control" name="institucion[]" placeholder="Nombre de la institución">
            </div>
        </div>
        <div class="row">
            <div class="col-md-6 mb-3">
                <label for="fecha_inicio_edu">Fecha de Inicio</label>
                <input type="date" class="form-control" name="fecha_inicio_edu[]">
            </div>
            <div class="col-md-6 mb-3">
                <label for="fecha_fin_edu">Fecha de Fin</label>
                <input type="date" class="form-control" name="fecha_fin_edu[]">
                <div class="form-check mt-2">
                    <input class="form-check-input" type="checkbox" name="en_curso[]">
                    <label class="form-check-label">En curso</label>
                </div>
            </div>
        </div>
        <button type="button" class="btn btn-danger mb-3" onclick="this.parentElement.remove()">Eliminar</button>
    `;
    container.insertBefore(nuevaEducacion, container.lastElementChild);
}

function agregarHabilidad() {
    const container = document.getElementById('habilidadesContainer');
    const habilidadItem = document.createElement('div');
    habilidadItem.className = 'skill-item';
    habilidadItem.innerHTML = `
        <div class="form-floating mb-3">
            <input type="text" class="form-control" name="habilidades[]" placeholder=" ">
            <label>Habilidad</label>
        </div>
        <button type="button" class="btn-remove" onclick="this.parentElement.remove(); updatePreview();">
            <i class="fas fa-trash"></i> Eliminar
        </button>
    `;
    container.appendChild(habilidadItem);
    updatePreview();
}

async function procesarPago() {
    try {
        // Obtener los datos del formulario
        const formData = new FormData(document.getElementById('cvForm'));
        const data = {};
        formData.forEach((value, key) => {
            if (key.endsWith('[]')) {
                const baseKey = key.slice(0, -2);
                if (!data[baseKey]) {
                    data[baseKey] = [];
                }
                data[baseKey].push(value);
            } else {
                data[key] = value;
            }
        });

        // Guardar datos en localStorage
        localStorage.setItem('cv_data', JSON.stringify(data));
        
        // Crear preferencia de pago
        const response = await fetch('/create_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const result = await response.json();
        
        if (result.id) {
            // Redirigir al checkout de MercadoPago
            window.location.href = `https://www.mercadopago.com.ar/checkout/v1/redirect?preference_id=${result.id}`;
        } else {
            throw new Error('No se recibió el ID de preferencia');
        }
    } catch (error) {
        console.error('Error al procesar el pago:', error);
        alert('Hubo un error al procesar el pago. Por favor, intente nuevamente.');
    }
}
