# ./dm_sistema/urls.py
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,
    ProveedorCreateAPIView,                           # ← NUEVO ENDPOINT
)

urlpatterns = [
    path("operadores/validar/",   OperadorLoginAPIView.as_view(),               name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(),  name="operador-verificar"),
    path(
        "operadores/sesiones-activas-token/",
        OperadorSesionActivaTokenAPIView.as_view(),
        name="operador-sesion-por-token",
    ),
    path(
        "operadores/logout/",
        OperadorLogoutAPIView.as_view(),
        name="operador-logout",
    ),
    path(                                            # ← RUTA PARA INSERTAR PROVEEDOR
        "logistica/proveedores/crear/",
        ProveedorCreateAPIView.as_view(),
        name="proveedor-crear",
    ),
]
