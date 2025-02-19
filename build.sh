#!/bin/bash

# Instalar wkhtmltopdf y sus dependencias
apt-get update
apt-get install -y wkhtmltopdf
apt-get install -y xvfb
apt-get install -y libfontconfig1
apt-get install -y libxrender1

# Crear un enlace simbólico para wkhtmltopdf
ln -s /usr/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
