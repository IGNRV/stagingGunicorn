# ./configuracion/serializer.py

from rest_framework import serializers
from .models import Modulo, Menu, EmpresaModulo, EmpresaModuloMenu

class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = '__all__'  # O define una lista de campos específica

class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'

class EmpresaModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModulo
        fields = '__all__'

class EmpresaModuloMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModuloMenu
        fields = '__all__'
