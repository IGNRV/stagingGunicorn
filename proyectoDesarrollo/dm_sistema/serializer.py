# --------------------------------------------------------------------------- #
# ./dm_sistema/serializer.py                                                  #
# --------------------------------------------------------------------------- #
from rest_framework import serializers

from dm_sistema.models import Operador, Comuna, Region
from dm_logistica.models import (
    Proveedor,
    Bodega,
    BodegaTipo,
    TipoProducto,
    MarcaProducto,
    TipoMarcaProducto,        # ← NUEVO
)

# ------------------------------------------------------------------------- #
#  SERIALIZADORES PARA LOGIN / VERIFICACIÓN                                 #
# ------------------------------------------------------------------------- #
class OperadorLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50, trim_whitespace=True)
    password = serializers.CharField(max_length=128, write_only=True)


class OperadorVerificarSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50, trim_whitespace=True)
    cod_verificacion = serializers.CharField(max_length=255, trim_whitespace=True)


class OperadorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Operador
        fields = "__all__"

# ------------------------------------------------------------------------- #
#  SERIALIZADOR PROVEEDOR – SIN id_giro, CON giro (char)                    #
# ------------------------------------------------------------------------- #
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Proveedor
        fields = [
            "id",
            "giro",
            "descrip_giro",
            "id_empresa",
            "rut",
            "nombre_rs",
            "nombre_fantasia",
            "web",
            "fecha_alta",
            "modalidad_pago",
            "plazo_pago",
            "estado",
            "direccion",
            "id_comuna",
            "id_region",
            "proveedor_unico",
        ]


class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bodega
        fields = "__all__"


class BodegaTipoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BodegaTipo
        fields = "__all__"

# ------------------------------------------------------------------------- #
#  SERIALIZADOR TIPO PRODUCTO                                               #
# ------------------------------------------------------------------------- #
class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoProducto
        fields = [
            "id",
            "codigo_tipo_producto",
            "id_empresa",
            "nombre_tipo_producto",
            "estado",
            "correlativo_desde",
            "correlativo_hasta",
        ]

# ------------------------------------------------------------------------- #
#  SERIALIZADOR MARCA PRODUCTO                                              #
# ------------------------------------------------------------------------- #
class MarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MarcaProducto
        fields = [
            "id",
            "id_empresa",
            "nombre_marca_producto",
            "estado",
        ]

# ------------------------------------------------------------------------- #
#  SERIALIZADOR TIPO-MARCA PRODUCTO                                         #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoMarcaProducto
        fields = [
            "id",
            "id_empresa",
            "id_tipo_producto",
            "id_marca_producto",
        ]

# ------------------------------------------------------------------------- #
#  SERIALIZADOR COMUNA                                                      #
# ------------------------------------------------------------------------- #
class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comuna
        fields = "__all__"

# ------------------------------------------------------------------------- #
#  SERIALIZADOR REGION                                                      #
# ------------------------------------------------------------------------- #
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Region
        fields = "__all__"
