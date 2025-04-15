# ./proyectoDesarrollo/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Se incluye la app "operadores" (ya existente)
    path('operadores/', include('operadores.urls')),
    # Se incluye la app "coreempresas" con el prefijo "coreempresas/"
    path('coreempresas/', include('coreempresas.urls')),
    # Se incluyen las demás apps
    path('configuracion/', include('configuracion.urls')),
    path('tasks/', include('tasks.urls')),
]
