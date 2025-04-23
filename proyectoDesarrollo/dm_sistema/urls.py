# dm_sistema/urls.py

from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

from .views import (
    OperadorViewSet, OperadorBodegaViewSet,
    OperadorEmpresaModuloViewSet, OperadorEmpresaModuloMenuViewSet,
    OperadorGrupoViewSet, OperadorPuntoVentaViewSet,
    SesionViewSet, SesionActivaViewSet,
    OperadorByTokenViewSet,
    ProveedorEmpresaViewSet      # ← ya registrado
)

router = routers.DefaultRouter()
router.register(r'operadores', OperadorViewSet, basename='operadores')
router.register(r'operadores-bodegas', OperadorBodegaViewSet, basename='operadores-bodegas')
router.register(r'operadores-empresa-modulos', OperadorEmpresaModuloViewSet, basename='operadores-empresa-modulos')
router.register(r'operadores-empresa-modulos-menus', OperadorEmpresaModuloMenuViewSet, basename='operadores-empresa-modulos-menus')
router.register(r'operadores-grupos', OperadorGrupoViewSet, basename='operadores-grupos')
router.register(r'operadores-punto-venta', OperadorPuntoVentaViewSet, basename='operadores-punto-venta')
router.register(r'sesiones', SesionViewSet, basename='sesiones')
router.register(r'sesiones-activas', SesionActivaViewSet, basename='sesiones-activas')
router.register(r'proveedores-empresa', ProveedorEmpresaViewSet, basename='proveedores-empresa')

urlpatterns = [
    path('', include(router.urls)),
    path('docs/', include_docs_urls(title='Operadores API')),
    path('sesiones-activas-token/',
         OperadorByTokenViewSet.as_view({'get': 'get_by_cookie'}),
         name='sesiones-activas-token-cookie'),
    path('logout/',
         OperadorViewSet.as_view({'get': 'logout'}),
         name='logout'),
]
