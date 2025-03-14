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
            // Verificar tamaño máximo (2MB)
            if (file.size > 2 * 1024 * 1024) {
                alert('La imagen es demasiado grande. El tamaño máximo permitido es 2MB.');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const imageData = e.target.result;
                
                // Optimizar la imagen antes de guardarla
                optimizeImage(imageData, function(optimizedImage) {
                    previewImage.src = optimizedImage;
                    
                    // Guardar la imagen optimizada en localStorage
                    localStorage.setItem('profile_image', optimizedImage);
                    
                    // Actualizar vista previa del CV
                    updateCVPreview();
                    
                 });
            };
            reader.readAsDataURL(file);
        }
    });

    // Event listeners para otros campos
    document.querySelectorAll('input, textarea').forEach(input => {
        if (input.id !== 'profileImageInput') {
            input.addEventListener('input', function() {
                // Preservar la imagen al actualizar la vista previa
                updateCVPreview();
            });
        }
    });

    // Event listener para el selector de plantilla
    document.querySelectorAll('input[name="template_type"]').forEach(radio => {
        radio.addEventListener('change', updateCVPreview);
    });

    // Event listener para el selector de color de plantilla
    document.querySelectorAll('input[name="template_color"]').forEach(radio => {
        radio.addEventListener('change', updateCVPreview);
    });

    // Cargar datos guardados si existen
    loadSavedData();
    
    // Añadir event listeners para los botones de experiencia, educación y habilidades
    document.getElementById('agregarExperiencia').addEventListener('click', agregarExperiencia);
    document.getElementById('agregarEducacion').addEventListener('click', agregarEducacion);
    document.getElementById('agregarHabilidad').addEventListener('click', agregarHabilidad);
    
    // Event listener para el botón de generar PDF
    document.getElementById('generarPDF').addEventListener('click', generarPDF);
    
    // Event listener para el botón de pagar
    document.getElementById('pagarButton').addEventListener('click', procesarPago);
    
    // Inicializar con una experiencia, educación y habilidad vacías
    agregarExperiencia();
    agregarEducacion();
    agregarHabilidad();
    
    // Inicializar la vista previa
    updateCVPreview();
    
    // Inicializar MercadoPago si está disponible
    if (typeof MercadoPago !== 'undefined') {
        initMercadoPago();
    }
    
    // Event listener para la foto de perfil
    document.getElementById('profileImageInput').addEventListener('change', handleImageUpload);
});

function loadSavedData() {
    const savedImage = localStorage.getItem('profile_image');
    if (savedImage) {
        document.getElementById('previewImage').src = savedImage;
    }
    updateCVPreview();
}

function updateCVPreview() {
    try {
        // Obtener datos del formulario
        const formData = obtenerDatosFormulario();
        
        // Obtener tipo de plantilla seleccionada
        const templateType = document.querySelector('input[name="template_type"]:checked').value;
        
        // Obtener color seleccionado (solo para plantilla profesional)
        let templateColor = null;
        if (templateType === 'profesional') {
            const colorSelected = document.querySelector('input[name="template_color"]:checked');
            if (colorSelected) {
                templateColor = colorSelected.value;
            }
        }
        
        // Obtener imagen de perfil directamente del localStorage
        const profileImage = localStorage.getItem('profile_image');
        if (profileImage) {
            formData.profile_image = profileImage;
        }
        
        // Generar HTML según el tipo de plantilla
        let previewHTML = '';
        if (templateType === 'profesional') {
            previewHTML = generateProTemplate(formData, templateColor);
        } else {
            previewHTML = generateBasicTemplate(formData);
        }
        
        // Actualizar el contenedor de vista previa
        document.getElementById('cvPreview').innerHTML = previewHTML;
    } catch (error) {
        console.error('Error al actualizar la vista previa:', error.message);
    }
}

function generateBasicTemplate(data) {
    return `
    <div class="cv-preview template-basic">
        <div class="header-section">
            <div class="row g-0">
                <div class="col-md-9 col-sm-12">
                    <h1>${data.nombre || ''}</h1>
                    <div class="contact-info-basic">
                        <p>DNI: ${data.dni || ''}</p>
                        <p>Fecha de Nacimiento: ${data.fecha_nacimiento || ''}</p>
                        <p>Edad: ${data.edad || ''}</p>
                        <p>Email: ${data.email || ''} | Tel: ${data.telefono || ''} | Dirección: ${data.direccion || ''}</p>
                    </div>
                </div>
                ${data.profile_image ? `
                <div class="col-md-3 col-sm-12">
                    <div class="profile-image">
                        <img src="${data.profile_image}" alt="Foto de perfil">
                    </div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="content-section">
            ${data.resumen ? `
                <section class="mb-4">
                    <h2>Resumen Profesional</h2>
                    <div class="resumen-profesional">
                        <p>${data.resumen}</p>
                    </div>
                </section>
            ` : ''}

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

function generateProTemplate(data, templateColor) {
    return `
    <div class="cv-preview template-professional ${templateColor}">
        <div class="header-section">
            <div class="row g-0">
                <div class="col-md-9 col-sm-12">
                    <h1>${data.nombre || ''}</h1>
                    <div class="contact-info-professional">
                        <p>DNI: ${data.dni || ''}</p>
                        <p>Fecha de Nacimiento: ${data.fecha_nacimiento || ''}</p>
                        <p>Edad: ${data.edad || ''}</p>
                        <p>Email: ${data.email || ''} | Tel: ${data.telefono || ''} | Dirección: ${data.direccion || ''}</p>
                    </div>
                </div>
                ${data.profile_image ? `
                <div class="col-md-3 col-sm-12">
                    <div class="profile-image">
                        <img src="${data.profile_image}" alt="Foto de perfil">
                    </div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="content-section">
            ${data.resumen ? `
                <section class="mb-4">
                    <h2>Resumen Profesional</h2>
                    <div class="resumen-profesional">
                        <p>${data.resumen}</p>
                    </div>
                </section>
            ` : ''}

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

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
     
        const maxImageSize = 10 * 1024 * 1024; // 10 megas

        if (file.size > maxImageSize) {
            alert(`La imagen es demasiado grande. El tamaño máximo permitido es ${maxImageSize / (1024 * 1024)}MB.`);
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = e.target.result;
            
            // Optimizar la imagen antes de guardarla
            optimizeImage(imageData, function(optimizedImage) {
                const previewImage = document.getElementById('previewImage');
                previewImage.src = optimizedImage;
                
                // Guardar la imagen optimizada en localStorage
                localStorage.setItem('profile_image', optimizedImage);
                
                // Actualizar vista previa del CV
                updateCVPreview();
                 });
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

    // Obtener tipo de plantilla
    const templateType = document.querySelector('input[name="template_type"]:checked').value;
    
    // Obtener color seleccionado (solo para plantilla profesional)
    let templateColor = null;
    if (templateType === 'profesional') {
        const colorSelected = document.querySelector('input[name="template_color"]:checked');
        if (colorSelected) {
            templateColor = colorSelected.value;
        }
    }

    const cvData = {
        template_type: templateType,
        template_color: templateColor, // Añadir el color seleccionado
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
    if (profileImage && !profileImage.includes('default-profile')) {
        cvData.profile_image = profileImage;
    }

    return cvData;
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
        
        throw error;
    }
}

// Función para obtener datos del formulario
function obtenerDatosFormulario() {
    const form = document.getElementById('cvForm');
    const formData = new FormData(form);
    
    // Obtener tipo de plantilla y color
    const templateType = document.querySelector('input[name="template_type"]:checked').value;
    
    // Obtener color seleccionado (solo para plantilla profesional)
    let templateColor = null;
    if (templateType === 'profesional') {
        const colorSelected = document.querySelector('input[name="template_color"]:checked');
        if (colorSelected) {
            templateColor = colorSelected.value;
            
        }
    }
    
    const cvData = {
        template_type: templateType,
        template_color: templateColor,
        nombre: formData.get('nombre'),
        dni: formData.get('dni'),
        fecha_nacimiento: formData.get('fecha_nacimiento'),
        edad: formData.get('edad'),
        email: formData.get('email'),
        telefono: formData.get('telefono'),
        direccion: formData.get('direccion'),
        resumen: formData.get('resumen'),
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

    // Procesar Experiencia Laboral
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

    // SIEMPRE obtener la imagen de perfil del localStorage
    const profileImage = localStorage.getItem('profile_image');
    if (profileImage) {
        cvData.profile_image = profileImage;
    }

    // Guardar datos completos en localStorage incluyendo el color
    localStorage.setItem('cv_data', JSON.stringify(cvData));
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
            resumen: formData.get('resumen'),
            experiencia: [],
            educacion: [],
            habilidades: formData.getAll('habilidades[]').filter(h => h.trim())
        };


        // Procesar experiencia
        const empresas = formData.getAll('empresa[]');
        empresas.forEach((empresa, index) => {
            if (empresa.trim()) {
                
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
                template_type: data.template_type,
                template_color: document.querySelector('input[name="template_color"]:checked')?.value || 'azul-marino',
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
    
    // Listener para selectores de color (solo para plantilla profesional)
    document.querySelectorAll('input[name="template_color"]').forEach(colorRadio => {
        colorRadio.addEventListener('change', updatePreview);
    });
    
    // Listener para carga de imagen
    document.getElementById('profileImageInput').addEventListener('change', handleImageUpload);
});

async function generarPDF() {
    try {
        
        // Recuperar datos del formulario
        const form = document.getElementById('cvForm');
        const formData = new FormData(form);
        
        // Crear objeto con todos los datos
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
            habilidades: [],
            resumen: formData.get('resumen')
        };
        
        // Procesar experiencia
        const empresas = formData.getAll('empresa[]');
        empresas.forEach((empresa, index) => {
            if (empresa.trim()) {
                cvData.experiencia.push({
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
                cvData.educacion.push({
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
        
        // Procesar habilidades
        const habilidades = formData.getAll('habilidad[]');
        habilidades.forEach(habilidad => {
            if (habilidad.trim()) {
                cvData.habilidades.push(habilidad.trim());
            }
        });
        
        // Obtener imagen directamente del elemento img
        const previewImage = document.getElementById('previewImage');
        if (previewImage && previewImage.src && !previewImage.src.includes('default-profile')) {
            // Asegurarse de que la imagen esté optimizada
            await new Promise((resolve) => {
                optimizeImage(previewImage.src, (optimizedImage) => {
                    cvData.profile_image = optimizedImage;
                    resolve();
                });
            });
        } else {
            // Intentar obtener del localStorage como respaldo
            const storedImage = localStorage.getItem('profile_image');
            if (storedImage) {
                cvData.profile_image = storedImage;
            }
        }
        
        // Guardar en localStorage para futuras referencias
        localStorage.setItem('cv_data', JSON.stringify(cvData));
        
        const response = await fetch('/download_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cvData)
        });

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
// Función para agregar experiencia
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
// Función para agregar educación
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
// Función para agregar habilidad
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

// Función para optimizar la imagen
function optimizeImage(base64Image, callback) {
    
    // Detectar el formato de la imagen
    let imageFormat = 'image/jpeg'; // Formato predeterminado
    if (base64Image.startsWith('data:image/')) {
        const match = base64Image.match(/data:image\/([a-zA-Z]+);/);
        if (match && match[1]) {
            imageFormat = 'image/' + match[1].toLowerCase();
        }
    }
    
    const img = new Image();
    img.onload = function() {
        // Dimensiones máximas
        const maxWidth = 300;
        const maxHeight = 300;
        
        // Calcular nuevas dimensiones manteniendo la relación de aspecto
        let width = img.width;
        let height = img.height;
        
        if (width > height) {
            if (width > maxWidth) {
                height = Math.round(height * maxWidth / width);
                width = maxWidth;
            }
        } else {
            if (height > maxHeight) {
                width = Math.round(width * maxHeight / height);
                height = maxHeight;
            }
        }
        
        // Crear canvas para redimensionar
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        
        // Dibujar imagen redimensionada
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#FFFFFF'; // Fondo blanco para imágenes con transparencia
        ctx.fillRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        
        // Intentar mantener el formato original si es posible
        try {
            // Para PNG, mantener transparencia si es necesario
            if (imageFormat === 'image/png') {
                const optimizedImage = canvas.toDataURL('image/png');
                callback(optimizedImage);
                return;
            }
            
            // Para JPEG, usar alta calidad
            const optimizedImage = canvas.toDataURL('image/jpeg', 0.95);
            callback(optimizedImage);
        } catch (error) {
            console.error('[ERROR] Error al convertir imagen:', error);
            // Intentar con formato alternativo si el original falla
            try {
                // Si falló JPEG, intentar PNG
                if (imageFormat === 'image/jpeg') {
                    const pngImage = canvas.toDataURL('image/png');
                    callback(pngImage);
                } else {
                    // Si falló PNG u otro, intentar JPEG
                    const jpegImage = canvas.toDataURL('image/jpeg', 0.95);
                    callback(jpegImage);
                }
            } catch (error2) {
                console.error('[ERROR] Error al convertir con formato alternativo:', error2);
                // Devolver la imagen original si todo falla
                
                callback(base64Image);
            }
        }
    };
    
    // Manejar errores de carga
    img.onerror = function(error) {
        console.error('[ERROR] Error al cargar la imagen para optimizar:', error);
        // Devolver la imagen original si hay error
        callback(base64Image);
    };
    
    img.src = base64Image;
}

// Función para iniciar pago
async function iniciarPago() {
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
            resumen: formData.get('resumen'),
            experiencia: [],
            educacion: [],
            habilidades: formData.getAll('habilidades[]').filter(h => h.trim())
        };

        // Procesar experiencia
        const empresas = formData.getAll('empresa[]');
        empresas.forEach((empresa, index) => {
            if (empresa.trim()) {
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

// Función para descargar PDF directamente sin pago
async function descargarPDFDirecto() {
    try {
        
        // Recuperar datos del formulario
        const cvData = obtenerDatosFormulario();
        
        // Asegurarse de que la imagen esté incluida
        const profileImage = localStorage.getItem('profile_image');
        if (profileImage) {
            cvData.profile_image = profileImage;
        } 
        
        // Enviar solicitud al servidor
        const response = await fetch('/download_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cvData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar el PDF');
        }
        
        // Obtener el blob del PDF
        const blob = await response.blob();
        
        // Crear URL para el blob
        const url = window.URL.createObjectURL(blob);
        
        // Crear elemento <a> para descargar
        const a = document.createElement('a');
        a.href = url;
        a.download = 'cv.pdf';
        document.body.appendChild(a);
        
        // Hacer clic para descargar
        a.click();
        
        // Limpiar
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('[ERROR] Error al descargar PDF:', error);
        alert('Error al generar el PDF: ' + error.message);
    }
}

// Función para agregar resumen
function agregarResumen() {
    // Obtener los datos del formulario para enviar a la IA
    const datosFormulario = obtenerDatosFormulario();
    
    // Mostrar indicador de carga
    const resumenContainer = document.getElementById('resumenContainer');
    const loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'resumen-loading';
    loadingIndicator.className = 'text-center my-3';
    loadingIndicator.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Generando resumen con IA...</span></div><p class="mt-2">Generando resumen profesional con IA...</p>';
    
    resumenContainer.appendChild(loadingIndicator);
    
    // Preparar los datos para la IA
    const prompt = generarPromptParaIA(datosFormulario);
    
    
    // Llamar a la API de DeepSeek R1
    fetch('/generar_resumen_ia', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt })
    })
    .then(response => response.json())
    .then(data => {
        // Eliminar indicador de carga
        document.getElementById('resumen-loading').remove();
        
        // Actualizar el campo de resumen con la respuesta de la IA
        if (data.resumen) {
            document.getElementById('resumen').value = data.resumen;
            // Actualizar la vista previa
            updateCVPreview();
        } else {
            alert('No se pudo generar el resumen. Por favor, intenta de nuevo.');
        }
    })
    .catch(error => {
        console.error('Error al generar resumen con IA:', error);
        // Eliminar indicador de carga
        if (document.getElementById('resumen-loading')) {
            document.getElementById('resumen-loading').remove();
        }
        alert('Error al comunicarse con la IA. Por favor, intenta de nuevo más tarde.');
    });
}

// Función para generar el prompt para la IA basado en los datos del formulario
function generarPromptParaIA(datos) {
    let prompt = "Genera un resumen profesional conciso y atractivo para un CV basado en la siguiente información:\n\n";
    
    // Datos personales
    prompt += `Nombre: ${datos.nombre || 'No especificado'}\n`;
    if (datos.edad) prompt += `Edad: ${datos.edad}\n`;
    
    // Experiencia laboral
    if (datos.experiencia && datos.experiencia.length > 0) {
        prompt += "\nExperiencia laboral:\n";
        datos.experiencia.forEach((exp, index) => {
            prompt += `${index + 1}. ${exp.empresa || 'Empresa'} - ${exp.cargo || 'Cargo'} (${exp.periodo || 'Periodo no especificado'})\n`;
            if (exp.descripcion) prompt += `   Descripción: ${exp.descripcion}\n`;
        });
    }
    
    // Educación
    if (datos.educacion && datos.educacion.length > 0) {
        prompt += "\nEducación:\n";
        datos.educacion.forEach((edu, index) => {
            prompt += `${index + 1}. ${edu.titulo || 'Título'} - ${edu.institucion || 'Institución'} (${edu.año || 'Año no especificado'})\n`;
        });
    }
    
    // Habilidades
    if (datos.habilidades && datos.habilidades.length > 0) {
        prompt += "\nHabilidades: " + datos.habilidades.join(", ") + "\n";
    }
    
    prompt += "\nInstrucciones: Genera un resumen profesional de aproximadamente 3-4 oraciones que destaque la experiencia, formación y habilidades más relevantes. El tono debe ser profesional y orientado a resultados. No uses frases genéricas como 'Soy un profesional apasionado'. Enfócate en logros concretos y valor añadido.";
    
    return prompt;
}
