# CV Generador

Aplicación web para generar currículums vitae profesionales en formato PDF.

## Características

- Creación de CV con información personal, educación, experiencia laboral y habilidades
- Múltiples plantillas disponibles (básica: $5, profesional: $10)
- Exportación a PDF
- Interfaz de usuario intuitiva

## Tecnologías

- Python
- Flask
- FPDF
- Pillow (PIL)
- HTML/CSS/JavaScript

## Instalación

1. Clonar el repositorio:
```
git clone https://github.com/davidpereyra2016/cv-generador.git
cd cv-generador
```

2. Instalar dependencias:
```
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```
python app.py
```

4. Acceder a la aplicación en el navegador:
```
http://localhost:5000
```

## Flujo de Trabajo (GitFlow)

Este proyecto utiliza GitFlow como modelo de ramificación. La estructura de ramas es la siguiente:

### Ramas Principales
- `main`: Contiene el código en producción
- `develop`: Rama principal de desarrollo

### Ramas de Soporte
- `feature/*`: Para nuevas funcionalidades
- `release/*`: Para preparar nuevas versiones
- `hotfix/*`: Para correcciones urgentes en producción
- `bugfix/*`: Para correcciones de errores no críticos

### Proceso de Desarrollo

1. Para implementar una nueva funcionalidad:
   ```
   git checkout develop
   git pull
   git checkout -b feature/nombre-funcionalidad
   # Desarrollar la funcionalidad
   git add .
   git commit -m "feat: descripción de la funcionalidad"
   git push -u origin feature/nombre-funcionalidad
   # Crear Pull Request a develop en GitHub
   ```

2. Para más detalles sobre el flujo de trabajo, consultar el archivo `.gitflow`

## Licencia

Este proyecto está bajo la Licencia MIT.
