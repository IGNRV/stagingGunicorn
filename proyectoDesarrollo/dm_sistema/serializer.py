# ./dm_sistema/serializer.py
from rest_framework import serializers

from dm_sistema.models import Operador
from dm_logistica.models import Proveedor, Giro, Bodega


class OperadorLoginSerializer(serializers.Serializer):
    """
    Body:
    {
        "username": "",
        "password": ""
    }
    """
    username = serializers.CharField(max_length=50, trim_whitespace=True)
    password = serializers.CharField(max_length=128, write_only=True)


class OperadorVerificarSerializer(serializers.Serializer):
    """
    Body:
    {
        "username": "",
        "cod_verificacion": ""
    }
    """
    username = serializers.CharField(max_length=50, trim_whitespace=True)
    cod_verificacion = serializers.CharField(max_length=255, trim_whitespace=True)


class OperadorSerializer(serializers.ModelSerializer):
    """
    Serializa **todas** las columnas de dm_sistema.operador para
    reenviarlas al cliente tal cual las entrega la BD.
    """
    class Meta:
        model  = Operador
        fields = "__all__"


class ProveedorSerializer(serializers.ModelSerializer):
    """
    Serializa **todas** las columnas de dm_logistica.proveedor para
    reenviarlas al cliente tal cual las entrega la BD.
    """
    class Meta:
        model  = Proveedor
        fields = "__all__"


class GiroSerializer(serializers.ModelSerializer):
    """
    Serializa **todas** las columnas de dm_logistica.giro para
    reenviarlas al cliente tal cual las entrega la BD.
    """
    class Meta:
        model  = Giro
        fields = "__all__"


class BodegaSerializer(serializers.ModelSerializer):
    """
    Serializa **todas** las columnas de dm_logistica.bodega para
    reenviarlas al cliente tal cual las entrega la BD.
    """
    class Meta:
        model  = Bodega
        fields = "__all__"
