# ./dm_sistema/urls.py
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,
    ProveedorCreateAPIView,
    ProveedorListAPIView,
    ProveedorDetailAPIView,   # ← nuevo
    BodegaListAPIView,        # ← ya existente
)

urlpatterns = [
    path("operadores/validar/",   OperadorLoginAPIView.as_view(),               name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(),  name="operador-verificar"),
    path(
        "operadores/sesiones-activas-token/",
        OperadorSesionActivaTokenAPIView.as_view(),
        name="operador-sesion-por-token",
    ),
    path("operadores/logout/", OperadorLogoutAPIView.as_view(), name="operador-logout"),

    # ------------------------------------------------------------------ #
    #  ENDPOINTS LOGÍSTICA                                               #
    # ------------------------------------------------------------------ #
    path(
        "logistica/proveedores/crear/",
        ProveedorCreateAPIView.as_view(),
        name="proveedor-crear",
    ),
    path(
        "logistica/proveedores/",
        ProveedorListAPIView.as_view(),
        name="proveedor-listar",
    ),
    path(
        "logistica/proveedores/detalle/",
        ProveedorDetailAPIView.as_view(),
        name="proveedor-detalle",
    ),
    path(
        "logistica/bodegas/",
        BodegaListAPIView.as_view(),
        name="bodega-listar",
    ),
]
