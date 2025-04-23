# ./dm_sistema/urls.py
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
    OperadorSesionActivaTokenAPIView,
    OperadorLogoutAPIView,                     # ← nuevo import
)

urlpatterns = [
    path("operadores/validar/",   OperadorLoginAPIView.as_view(),               name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(),  name="operador-verificar"),
    path(
        "operadores/sesiones-activas-token/",
        OperadorSesionActivaTokenAPIView.as_view(),
        name="operador-sesion-por-token",
    ),
    path(                                 # ← nueva ruta
        "operadores/logout/",
        OperadorLogoutAPIView.as_view(),
        name="operador-logout",
    ),
]
