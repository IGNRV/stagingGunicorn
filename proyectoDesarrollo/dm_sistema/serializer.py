# ./dm_sistema/serializer.py

from rest_framework import serializers


class OperadorLoginSerializer(serializers.Serializer):
    """
    Valida la estructura del body JSON:
    {
        "username": "",
        "password": ""
    }
    """
    username = serializers.CharField(
        max_length=50,
        required=True,
        trim_whitespace=True
    )
    password = serializers.CharField(
        max_length=128,         # tamaño suficiente para la clave en texto plano
        required=True,
        write_only=True         # nunca se devuelve al cliente
    )
