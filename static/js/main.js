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

// Event listeners para los inputs
document.addEventListener('DOMContentLoaded', function() {
    // Manejar la carga de imagen de perfil
    const profileImageInput = document.getElementById('profileImageInput');
    const previewImage = document.getElementById('previewImage');

    profileImageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageData = e.target.result;
                previewImage.src = imageData;
                localStorage.setItem('profile_image', imageData);
                updateCVPreview();
            };
            reader.readAsDataURL(file);
        }
    });

    // Event listeners para otros campos
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('input', updateCVPreview);
    });

    // Event listener para el selector de plantilla
    document.querySelectorAll('input[name="template"]').forEach(radio => {
        radio.addEventListener('change', updateCVPreview);
    });

    // Cargar datos guardados si existen
    loadSavedData();
});

function loadSavedData() {
    const savedImage = localStorage.getItem('profile_image');
    if (savedImage) {
        document.getElementById('previewImage').src = savedImage;
    }
    updateCVPreview();
}

function updateCVPreview() {
    const formData = getFormData();
    const template = document.querySelector('input[name="template"]:checked').value;
    const previewContainer = document.getElementById('cvPreview');
    
    let previewHTML = '';
    if (template === 'profesional') {
        previewHTML = `
            <div class="cv-preview professional-template">
                <div class="header-section">
                    <div class="profile-info">
                        <h1>${formData.nombre || 'Nombre Completo'}</h1>
                        <div class="contact-info">
                            <div class="primary-contact">
                                ${formData.email ? `<p>Email: ${formData.email}</p>` : ''}
                                ${formData.telefono ? `<p>Tel: ${formData.telefono}</p>` : ''}
                                ${formData.direccion ? `<p>${formData.direccion}</p>` : ''}
                            </div>
                            <div class="secondary-contact">
                                ${formData.dni ? `<p>DNI: ${formData.dni}</p>` : ''}
                                ${formData.fecha_nacimiento ? `<p>Fecha de Nacimiento: ${formData.fecha_nacimiento}</p>` : ''}
                                ${formData.edad ? `<p>Edad: ${formData.edad}</p>` : ''}
                            </div>
                        </div>
                    </div>
                    ${formData.profile_image ? `
                    <div class="profile-image">
                        <img src="${formData.profile_image}" alt="Foto de perfil">
                    </div>
                    ` : ''}
                </div>

                <!-- Experiencia Laboral -->
                <div class="section">
                    <h2>Experiencia Laboral</h2>
                    ${formData.experiencia.map(exp => `
                        <div class="experience-item">
                            <h3>${exp.empresa || ''}</h3>
                            <p class="position">${exp.cargo || ''}</p>
                            <p class="period">${exp.periodo || ''}</p>
                            ${exp.descripcion ? `<p class="description">${exp.descripcion}</p>` : ''}
                        </div>
                    `).join('')}
                </div>

                <!-- Educación -->
                <div class="section">
                    <h2>Educación</h2>
                    ${formData.educacion.map(edu => `
                        <div class="education-item">
                            <h3>${edu.titulo || ''}</h3>
                            <p class="institution">${edu.institucion || ''}</p>
                            <p class="year">${edu.año || ''}</p>
                        </div>
                    `).join('')}
                </div>

                <!-- Habilidades -->
                ${formData.habilidades.length > 0 ? `
                    <div class="section">
                        <h2>Habilidades</h2>
                        <div class="skills-section">
                            ${formData.habilidades.map(hab => `
                                <span class="skill-item">${hab}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>`;
    } else {
        // Template básico
        previewHTML = `
            <div class="cv-preview basic-template">
                <h1 class="text-center">${formData.nombre || 'Nombre Completo'}</h1>
                <div class="contact-info text-center">
                    ${formData.email ? `<p>Email: ${formData.email}</p>` : ''}
                    ${formData.telefono ? `<p>Tel: ${formData.telefono}</p>` : ''}
                    ${formData.direccion ? `<p>${formData.direccion}</p>` : ''}
                </div>
                <!-- Resto del contenido básico -->
            </div>`;
    }
    
    previewContainer.innerHTML = previewHTML;
}

function getFormData() {
    const formData = {
        nombre: document.getElementById('nombre')?.value || '',
        email: document.getElementById('email')?.value || '',
        telefono: document.getElementById('telefono')?.value || '',
        direccion: document.getElementById('direccion')?.value || '',
        dni: document.getElementById('dni')?.value || '',
        fecha_nacimiento: document.getElementById('fecha_nacimiento')?.value || '',
        edad: document.getElementById('edad')?.value || '',
        experiencia: [],
        educacion: [],
        habilidades: [],
        profile_image: localStorage.getItem('profile_image') || null,
        template_type: document.querySelector('input[name="template"]:checked')?.value || 'basico'
    };
    
    // Obtener experiencia laboral
    document.querySelectorAll('.experiencia-item').forEach(item => {
        formData.experiencia.push({
            empresa: item.querySelector('[name="empresa"]')?.value || '',
            cargo: item.querySelector('[name="cargo"]')?.value || '',
            periodo: item.querySelector('[name="periodo"]')?.value || '',
            descripcion: item.querySelector('[name="descripcion"]')?.value || ''
        });
    });
    
    // Obtener educación
    document.querySelectorAll('.educacion-item').forEach(item => {
        formData.educacion.push({
            titulo: item.querySelector('[name="titulo"]')?.value || '',
            institucion: item.querySelector('[name="institucion"]')?.value || '',
            año: item.querySelector('[name="año"]')?.value || ''
        });
    });
    
    // Obtener habilidades
    document.querySelectorAll('.habilidad-item input').forEach(item => {
        if (item.value.trim()) {
            formData.habilidades.push(item.value.trim());
        }
    });
    
    return formData;
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
        template_type: document.querySelector('input[name="template_type"]:checked').value,
        nombre: formData.get('nombre'),
        dni: formData.get('dni'),
        fecha_nacimiento: formData.get('fecha_nacimiento'),
        edad: formData.get('edad'),
        email: formData.get('email'),
        telefono: formData.get('telefono'),
        direccion: formData.get('direccion'),
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
            cvData.experiencia.push({
                empresa: empresa,
                cargo: cargos[index] || '',
                periodo: `${fechasInicio[index] || ''} - ${trabajoActual[index] === 'on' ? 'Presente' : fechasFin[index] || ''}`,
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
            cvData.educacion.push({
                titulo: titulo,
                institucion: instituciones[index] || '',
                año: `${fechasInicioEdu[index] || ''} - ${enCurso[index] === 'on' ? 'En curso' : fechasFinEdu[index] || ''}`
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
    <div class="cv-preview template-basic">
        <div class="header-section">
            <div class="row align-items-center">
                <div class="col-md-9">
                    <div class="profile-info">
                        <h1 class="text-black-basic">${data.nombre || ''}</h1>
                        <div class="contact-info-basic">
                            ${data.email ? `<p>Email: ${data.email}</p>` : ''}
                            ${data.telefono ? `<p>Telefono: ${data.telefono}</p>` : ''}
                            ${data.direccion ? `<p>Dirección: ${data.direccion}</p>` : ''}
                            ${data.dni ? `<p>DNI: ${data.dni}</p>` : ''}
                            ${data.fecha_nacimiento ? `<p>Fecha de nacimiento: ${data.fecha_nacimiento}</p>` : ''}
                            ${data.edad ? `<p>Edad: ${data.edad}</p>` : ''}
                        </div>
                    </div>
                </div>
                ${data.profile_image ? `
                <div class="col-md-3">
                    <div class="profile-image">
                        <img src="${data.profile_image}" alt="Foto de perfil" class="img-fluid">
                    </div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="content-section">
            ${data.experiencia && data.experiencia.length ? `
                <section class="mb-4">
                    <h2>Experiencia Laboral</h2>
                    ${data.experiencia.map(exp => `
                        <div class="experience-item">
                            <h3>${exp.cargo}</h3>
                            <div class="company">${exp.empresa}</div>
                            <div class="period">${exp.periodo}</div>
                            ${exp.descripcion ? `<div class="description">${exp.descripcion}</div>` : ''}
                        </div>
                    `).join('')}
                </section>
            ` : ''}

            ${data.educacion && data.educacion.length ? `
                <section class="mb-4">
                    <h2>Educación</h2>
                    ${data.educacion.map(edu => `
                        <div class="education-item">
                            <h3>${edu.titulo}</h3>
                            <div class="institution">${edu.institucion}</div>
                            <div class="year">${edu.año}</div>
                        </div>
                    `).join('')}
                </section>
            ` : ''}

            ${data.habilidades && data.habilidades.length ? `
                <section class="mb-4">
                    <h2>Habilidades</h2>
                    <div class="skills-section">
                        ${data.habilidades.map(skill => `
                            <span class="skill-item">${skill}</span>
                        `).join('')}
                    </div>
                </section>
            ` : ''}
        </div>
    </div>`;
}

function generateProTemplate(data) {
    return `
    <div class="cv-preview template-professional">
        <div class="header-section">
            <div class="row align-items-center">
                <div class="col-md-9">
                    <div class="profile-info">
                        <h1 class="text-black-professional">${data.nombre || ''}</h1>
                        <div class="contact-info-professional">
                            ${data.email ? `<p>Email: ${data.email}</p>` : ''}
                            ${data.telefono ? `<p>Telefono: ${data.telefono}</p>` : ''}
                            ${data.direccion ? `<p>Dirección: ${data.direccion}</p>` : ''}
                            ${data.dni ? `<p>DNI: ${data.dni}</p>` : ''}
                            ${data.fecha_nacimiento ? `<p>Fecha de nacimiento: ${data.fecha_nacimiento}</p>` : ''}
                            ${data.edad ? `<p>Edad: ${data.edad}</p>` : ''}
                        </div>
                    </div>
                </div>
                ${data.profile_image ? `
                <div class="col-md-3">
                    <div class="profile-image">
                        <img src="${data.profile_image}" alt="Foto de perfil" class="img-fluid">
                    </div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="content-section">
            ${data.experiencia && data.experiencia.length ? `
                <section class="mb-4">
                    <h2>Experiencia Laboral</h2>
                    ${data.experiencia.map(exp => `
                        <div class="experience-item">
                            <h3>${exp.cargo}</h3>
                            <div class="company">${exp.empresa}</div>
                            <div class="period">${exp.periodo}</div>
                            ${exp.descripcion ? `<div class="description">${exp.descripcion}</div>` : ''}
                        </div>
                    `).join('')}
                </section>
            ` : ''}

            ${data.educacion && data.educacion.length ? `
                <section class="mb-4">
                    <h2>Educación</h2>
                    ${data.educacion.map(edu => `
                        <div class="education-item">
                            <h3>${edu.titulo}</h3>
                            <div class="institution">${edu.institucion}</div>
                            <div class="year">${edu.año}</div>
                        </div>
                    `).join('')}
                </section>
            ` : ''}

            ${data.habilidades && data.habilidades.length ? `
                <section class="mb-4">
                    <h2>Habilidades</h2>
                    <div class="skills-section">
                        ${data.habilidades.map(skill => `
                            <span class="skill-item">${skill}</span>
                        `).join('')}
                    </div>
                </section>
            ` : ''}
        </div>
    </div>`;
}

// Función para guardar datos del formulario en el servidor
async function guardarDatosFormulario() {
    try {
        const cvData = obtenerDatosFormulario();
        
        const response = await fetch('/save_form_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cvData)
        });
        
        if (!response.ok) {
            throw new Error('Error al guardar los datos del formulario');
        }
        
        const data = await response.json();
        return data.form_id;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Función para obtener datos del formulario
function obtenerDatosFormulario() {
    const form = document.getElementById('cvForm');
    const formData = new FormData(form);
    
    const cvData = {
        template_type: document.querySelector('input[name="template_type"]:checked').value,
        nombre: formData.get('nombre'),
        dni: formData.get('dni'),
        fecha_nacimiento: formData.get('fecha_nacimiento'),
        edad: formData.get('edad'),
        email: formData.get('email'),
        telefono: formData.get('telefono'),
        direccion: formData.get('direccion'),
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
            cvData.experiencia.push({
                empresa: empresa,
                cargo: cargos[index] || '',
                periodo: `${fechasInicio[index] || ''} - ${trabajoActual[index] === 'on' ? 'Presente' : fechasFin[index] || ''}`,
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
            cvData.educacion.push({
                titulo: titulo,
                institucion: instituciones[index] || '',
                año: `${fechasInicioEdu[index] || ''} - ${enCurso[index] === 'on' ? 'En curso' : fechasFinEdu[index] || ''}`
            });
        }
    });

    // Agregar imagen de perfil si existe
    const profileImage = document.getElementById('previewImage').src;
    if (profileImage && !profileImage.includes('default-profile1.png')) {
        cvData.profile_image = profileImage;
    }

    return cvData;
}

// Función unificada procesarPago para incluir form_id como external_reference
async function procesarPago() {
    try {
        // Obtener los datos del formulario
        const formData = new FormData(document.getElementById('cvForm'));
        
        // Crear objeto con los datos
        const data = {
            template_type: document.querySelector('input[name="template_type"]:checked').value,
            nombre: formData.get('nombre'),
            dni: formData.get('dni'),
            fecha_nacimiento: formData.get('fecha_nacimiento'),
            edad: formData.get('edad'),
            email: formData.get('email'),
            telefono: formData.get('telefono'),
            direccion: formData.get('direccion'),
            experiencia: [],
            educacion: [],
            habilidades: formData.getAll('habilidades[]').filter(h => h.trim())
        };

        console.log('[DEBUG] Datos básicos recopilados:', data);

        // Procesar experiencia
        const empresas = formData.getAll('empresa[]');
        empresas.forEach((empresa, index) => {
            if (empresa.trim()) {
                console.log(`[DEBUG] Procesando experiencia ${index}:`, empresa);
                data.experiencia.push({
                    empresa: empresa.trim(),
                    cargo: formData.getAll('cargo[]')[index]?.trim() || '',
                    periodo: `${formData.getAll('fecha_inicio[]')[index]?.trim() || ''} - ${
                        formData.getAll('trabajo_actual[]')[index] === 'on' 
                        ? 'Presente' 
                        : formData.getAll('fecha_fin[]')[index]?.trim() || ''
                    }`,
                    descripcion: formData.getAll('descripcion[]')[index]?.trim() || ''
                });
            }
        });

        // Procesar educación
        const titulos = formData.getAll('titulo[]');
        titulos.forEach((titulo, index) => {
            if (titulo.trim()) {
                console.log(`[DEBUG] Procesando educación ${index}:`, titulo);
                data.educacion.push({
                    titulo: titulo.trim(),
                    institucion: formData.getAll('institucion[]')[index]?.trim() || '',
                    año: `${formData.getAll('fecha_inicio_edu[]')[index]?.trim() || ''} - ${
                        formData.getAll('en_curso[]')[index] === 'on'
                        ? 'En curso'
                        : formData.getAll('fecha_fin_edu[]')[index]?.trim() || ''
                    }`
                });
            }
        });

        console.log('[DEBUG] Datos completos a enviar:', JSON.stringify(data, null, 2));
        
        // Guardar en localStorage
        localStorage.setItem('cv_data', JSON.stringify(data));

        // Primero guardar los datos del formulario para obtener un form_id
        const saveResponse = await fetch('/save_form_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!saveResponse.ok) {
            throw new Error('Error al guardar los datos del formulario');
        }
        
        const saveResult = await saveResponse.json();
        const formId = saveResult.form_id;

        if (!formId) {
            throw new Error('No se recibió el ID del formulario');
        }
        
        // Crear preferencia de pago
        const response = await fetch('/create_preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                template_type: data.template_type, // Usar el mismo valor de la plantilla
                external_reference: formId
            })
        });

        if (!response.ok) {
            throw new Error('Error al crear preferencia de pago');
        }

        const preference = await response.json();
        
        // Redirigir a MercadoPago
        window.location.href = preference.init_point;
        
    } catch (error) {
        console.error('[ERROR] Error al procesar el pago:', error);
        alert('Error al procesar el pago. Por favor, intente nuevamente.');
    }
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

async function generarPDF() {
    try {
        // Recuperar datos del localStorage
        const cvData = localStorage.getItem('cv_data');
        console.log('[DEBUG] Datos recuperados de localStorage:', cvData);
        
        if (!cvData) {
            throw new Error('No se encontraron datos del CV');
        }

        // Enviar datos al servidor para generar PDF
        const response = await fetch('/download_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: cvData
        });

        console.log('[DEBUG] Respuesta del servidor:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar el PDF');
        }

        // Obtener el blob del PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'cv.pdf';
        document.body.appendChild(a);
        a.click();
        
        // Limpiar
        setTimeout(() => {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 100);

    } catch (error) {
        console.error('[ERROR] Error al generar el PDF:', error);
        alert('Hubo un error al generar el PDF: ' + error.message);
    }
}

// Verificar si venimos de un pago exitoso y generar PDF
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('status') === 'approved') {
        generarPDF();
    }
});
