# dm_sistema/serializer.py

from rest_framework import serializers
from .models import (
    Operador, OperadorBodega, OperadorEmpresaModulo, 
    OperadorEmpresaModuloMenu, OperadorGrupo, OperadorPuntoVenta,
    Sesion, SesionActiva
)
from dm_logistica.models import Proveedor  # ← import para el nuevo serializer

class OperadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operador
        fields = '__all__'

class OperadorBodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorBodega
        fields = '__all__'

class OperadorEmpresaModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorEmpresaModulo
        fields = '__all__'

class OperadorEmpresaModuloMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorEmpresaModuloMenu
        fields = '__all__'

class OperadorGrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorGrupo
        fields = '__all__'

class OperadorPuntoVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperadorPuntoVenta
        fields = '__all__'

class SesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sesion
        fields = '__all__'

class SesionActivaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionActiva
        fields = '__all__'

# ─────────────────────────────────────────────────────────────────────────────
# NUEVO: Serializer para Proveedor
# ─────────────────────────────────────────────────────────────────────────────
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'
