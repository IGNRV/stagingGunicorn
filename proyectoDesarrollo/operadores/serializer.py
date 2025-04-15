# ./operadores/serializer.py

from rest_framework import serializers
from .models import (
    Operador, OperadorBodega, OperadorEmpresaModulo, 
    OperadorEmpresaModuloMenu, OperadorGrupo, OperadorPuntoVenta,
    Sesion, SesionActiva
    # SesionEjecutivo ya NO existe
)

class OperadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operador
        fields = '__all__'  # O especifica los campos que quieras

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

# Se elimina la clase SesionEjecutivoSerializer, ya que no existe el modelo
