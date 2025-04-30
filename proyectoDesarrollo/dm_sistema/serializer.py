# === ./dm_sistema/serializer.py ===
from rest_framework import serializers

from dm_sistema.models import Operador, Comuna, Region
from dm_logistica.models import (
    Proveedor,
    Bodega,
    BodegaTipo,
    TipoProducto,
    MarcaProducto,
    TipoMarcaProducto,
    ModeloProducto,
)
from dm_logistica.serializer import ModeloProductoSerializer


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


class MarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MarcaProducto
        fields = [
            "id",
            "id_empresa",
            "nombre_marca_producto",
            "estado",
        ]


class TipoMarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoMarcaProducto
        fields = [
            "id",
            "id_empresa",
            "id_tipo_producto",
            "id_marca_producto",
        ]


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Comuna
        fields = "__all__"


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Region
        fields = "__all__"


# ------------------------------------------------------------------------- #
#  NUEVO SERIALIZER PARA EL ENDPOINT DE BODEGAS “COMPLETAS”                #
# ------------------------------------------------------------------------- #
class BodegaCompletaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    id_empresa = serializers.IntegerField()
    nombre_tipo_bodega = serializers.CharField()
    estado_bodega = serializers.IntegerField()
    nombre_bodega = serializers.CharField()
