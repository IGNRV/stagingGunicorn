# ./dm_sistema/urls.py
from django.urls import path

from .views import (
    OperadorLoginAPIView,
    OperadorCodigoVerificacionAPIView,
)

urlpatterns = [
    path("operadores/validar/",  OperadorLoginAPIView.as_view(),            name="operador-login"),
    path("operadores/verificar/", OperadorCodigoVerificacionAPIView.as_view(), name="operador-verificar"),
]
