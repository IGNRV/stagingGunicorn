# ./dm_sistema/urls.py
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,
    ProveedorCreateAPIView,        # ← crear proveedor
    ProveedorListAPIView,          # ← **NUEVO** listar proveedores
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
    # ------------------------------------------------------------------ #
    #  ENDPOINTS LOGÍSTICA – PROVEEDOR                                   #
    # ------------------------------------------------------------------ #
    path(
        "logistica/proveedores/crear/",
        ProveedorCreateAPIView.as_view(),
        name="proveedor-crear",
    ),
    path(
        "logistica/proveedores/",
        ProveedorListAPIView.as_view(),        # GET con cookie → lista
        name="proveedor-listar",
    ),
]
