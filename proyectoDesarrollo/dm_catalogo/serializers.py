# dm_catalogo/serializers.py
from rest_framework import serializers
from .models import TipoMoneda

class TipoMonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoMoneda
        # Incluye todos los campos del modelo, incluido el id implícito
        fields = "__all__"
