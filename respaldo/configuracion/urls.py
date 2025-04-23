# ./configuracion/urls.py
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from .views import (
    ModuloViewSet,
    MenuViewSet,
    EmpresaModuloViewSet,
    EmpresaModuloMenuViewSet
)

router = routers.DefaultRouter()
router.register(r'modulos', ModuloViewSet, basename='modulos')
router.register(r'menus', MenuViewSet, basename='menus')
router.register(r'empresa-modulos', EmpresaModuloViewSet, basename='empresa-modulos')
router.register(r'empresa-modulos-menus', EmpresaModuloMenuViewSet, basename='empresa-modulos-menus')

urlpatterns = [
    path('', include(router.urls)),
    path('docs/', include_docs_urls(title='Configuración API')),
]
