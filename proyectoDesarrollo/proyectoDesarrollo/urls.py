# ./proyectoDesarrollo/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # ▸ Rutas de la nueva lógica bajo dm_sistema
    path('dm_sistema/', include('dm_sistema.urls')),
]

# Solo para desarrollo local; en producción lo sirve Nginx
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )