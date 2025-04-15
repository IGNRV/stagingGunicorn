#!/bin/bash
# Nombre del proyecto
NAME="proyectoDesarrollo"
# Directorio del proyecto (ajusta la ruta a tu proyecto)
DJANGODIR="/home/ignrv/proyectos/Gunicorn/proyectoDesarrollo"
# Directorio del entorno virtual (ajusta la ruta a tu venv)
VENV="/home/ignrv/proyectos/Gunicorn/venv/bin/activate"
# Número de workers (ajusta según tus necesidades)
NUM_WORKERS=3
# Módulo WSGI de Django
DJANGO_WSGI_MODULE="proyectoDesarrollo.wsgi:application"

echo "Iniciando Gunicorn para $NAME como $(whoami)"

# Entrar al directorio del proyecto
cd $DJANGODIR || exit
# Activar el entorno virtual
source $VENV

# Exportar la variable de entorno de configuración (si no está ya definida)
export DJANGO_SETTINGS_MODULE=proyectoDesarrollo.settings

# Iniciar Gunicorn
exec gunicorn $DJANGO_WSGI_MODULE \
  --name $NAME \
  --workers $NUM_WORKERS \
  --bind 0.0.0.0:8000 \
  --log-level=info \
  --log-file=-
