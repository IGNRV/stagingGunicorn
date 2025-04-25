# --------------------------------------------------------------------------- #
# ./dm_sistema/urls.py                                                        #
# --------------------------------------------------------------------------- #
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,
    # -------- LOGÍSTICA -------- #
    ProveedorCreateAPIView,
    ProveedorListAPIView,
    ProveedorDetailAPIView,
    ProveedorUpdateAPIView,
    BodegaListAPIView,
    BodegaUpdateAPIView,            # ← NUEVO
)

urlpatterns = [
    # --------------------------- OPERADORES ----------------------------- #
    path("operadores/validar/",   OperadorLoginAPIView.as_view(),              name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(), name="operador-verificar"),
    path(
        "operadores/sesiones-activas-token/",
        OperadorSesionActivaTokenAPIView.as_view(),
        name="operador-sesion-por-token",
    ),
    path("operadores/logout/", OperadorLogoutAPIView.as_view(), name="operador-logout"),

    # --------------------------- LOGÍSTICA – PROVEEDOR ------------------ #
    path("logistica/proveedores/crear/",  ProveedorCreateAPIView.as_view(),  name="proveedor-crear"),
    path("logistica/proveedores/",        ProveedorListAPIView.as_view(),    name="proveedor-listar"),
    path("logistica/proveedores/detalle/",ProveedorDetailAPIView.as_view(),  name="proveedor-detalle"),
    path("logistica/proveedores/editar/", ProveedorUpdateAPIView.as_view(),  name="proveedor-editar"),

    # --------------------------- LOGÍSTICA – BODEGA --------------------- #
    path("logistica/bodegas/",            BodegaListAPIView.as_view(),       name="bodega-listar"),
    path("logistica/bodegas/editar/",     BodegaUpdateAPIView.as_view(),     name="bodega-editar"),  # ← NEW
]
