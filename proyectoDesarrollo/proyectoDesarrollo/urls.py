# ./proyectoDesarrollo/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ▸ Rutas de la nueva lógica bajo dm_sistema
    path('dm_sistema/', include('dm_sistema.urls')),

]
