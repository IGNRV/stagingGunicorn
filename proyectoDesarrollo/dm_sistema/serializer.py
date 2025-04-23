# ./dm_sistema/serializer.py
from rest_framework import serializers


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
