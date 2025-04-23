# ./dm_sistema/urls.py

from django.urls import path

from .views import OperadorLoginAPIView

urlpatterns = [
    path(
        "operadores/validar/",
        OperadorLoginAPIView.as_view(),
        name="operador-login",
    ),
]
