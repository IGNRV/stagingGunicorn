# dm_catalogo/urls.py
from django.urls import path
from .views import TipoMonedaListAPIView

urlpatterns = [
    # Endpoint para listar tipos de moneda
    path(
        "tipos-moneda/",
        TipoMonedaListAPIView.as_view(),
        name="tipo-moneda-listar"
    ),
]
