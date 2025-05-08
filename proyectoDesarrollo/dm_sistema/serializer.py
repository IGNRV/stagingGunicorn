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
    IdentificadorSerie,
    UnidadMedida,
    Atributo,
    OrdenCompra,
    SolicitudCompra,        # ← NUEVO
    TipoSolicitud,          # ← NUEVO
)
from dm_logistica.serializer import ModeloProductoSerializer


# ------------------------------------------------------------------------- #
#  SERIALIZERS EXISTENTES PARA LOGIN, BODEGAS, LOGÍSTICA, ETC.              #
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


class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Proveedor
        fields = [
            "id", "giro", "descrip_giro", "id_empresa", "rut",
            "nombre_rs", "nombre_fantasia", "web", "fecha_alta",
            "modalidad_pago", "plazo_pago", "estado",
            "direccion", "id_comuna", "id_region", "proveedor_unico",
        ]


class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Bodega
        fields = "__all__"


class BodegaTipoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BodegaTipo
        fields = "__all__"


class TipoSolicitudSerializer(serializers.ModelSerializer):  # ← NUEVO
    class Meta:
        model  = TipoSolicitud
        fields = "__all__"


class TipoProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoProducto
        fields = [
            "id", "codigo_tipo_producto", "id_empresa", "nombre_tipo_producto",
            "estado", "correlativo_desde", "correlativo_hasta",
        ]


class MarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MarcaProducto
        fields = [
            "id", "id_empresa", "nombre_marca_producto", "estado",
        ]


class TipoMarcaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoMarcaProducto
        fields = [
            "id", "id_empresa", "id_tipo_producto", "id_marca_producto",
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
#  BODEGAS “COMPLETAS” (JOIN)                                               #
# ------------------------------------------------------------------------- #
class BodegaCompletaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    id_empresa = serializers.IntegerField()
    nombre_tipo_bodega = serializers.CharField()
    estado_bodega = serializers.IntegerField()
    nombre_bodega = serializers.CharField()


# ------------------------------------------------------------------------- #
#  MODELO PRODUCTO – JOIN COMPLETO (sin imagen)                             #
# ------------------------------------------------------------------------- #
class ModeloProductoCompletoSerializer(serializers.Serializer):
    id_modelo_producto      = serializers.IntegerField()
    id_empresa              = serializers.IntegerField()
    codigo_tipo_producto    = serializers.CharField()
    nombre_tipo_producto    = serializers.CharField()
    nombre_marca_producto   = serializers.CharField()
    nombre_unidad_medida    = serializers.CharField()
    id_identificador_serie  = serializers.IntegerField()
    codigo_interno          = serializers.CharField(allow_null=True, allow_blank=True)
    sku                     = serializers.CharField(allow_null=True, allow_blank=True)
    sku_codigo              = serializers.CharField(allow_null=True, allow_blank=True)
    nombre_modelo           = serializers.CharField()
    descripcion             = serializers.CharField(allow_null=True, allow_blank=True)
    imagen                  = serializers.CharField(allow_null=True, allow_blank=True)
    estado                  = serializers.IntegerField()
    producto_seriado        = serializers.IntegerField()
    nombre_comercial        = serializers.CharField(allow_null=True, allow_blank=True)
    despacho_express        = serializers.IntegerField()
    rebaja_consumo          = serializers.IntegerField(allow_null=True)
    dias_rebaja_consumo     = serializers.IntegerField(allow_null=True)
    orden_solicitud_despacho= serializers.IntegerField(allow_null=True)


# ------------------------------------------------------------------------- #
#  MODELO PRODUCTO – JOIN + IMAGEN BASE64                                   #
# ------------------------------------------------------------------------- #
class ModeloProductoCompletoDetalleSerializer(ModeloProductoCompletoSerializer):
    imagen_base64 = serializers.CharField(allow_null=True, read_only=True)


# ------------------------------------------------------------------------- #
#  IDENTIFICADOR DE SERIE & UNIDAD DE MEDIDA                                #
# ------------------------------------------------------------------------- #
class IdentificadorSerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentificadorSerie
        fields = [
            "id",
            "nombre_serie",
            "estado_serie",
        ]


class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = "__all__"


# ------------------------------------------------------------------------- #
#  NUEVO SERIALIZER → JOIN TIPO-MARCA-PRODUCTO                              #
# ------------------------------------------------------------------------- #
class TipoMarcaProductoJoinSerializer(serializers.Serializer):
    id_tipo_marca_producto = serializers.IntegerField()
    id_empresa             = serializers.IntegerField()
    codigo_tipo_producto   = serializers.CharField()
    nombre_tipo_producto   = serializers.CharField()
    nombre_marca_producto  = serializers.CharField()


# ------------------------------------------------------------------------- #
#  --- NUEVO ENDPOINT ATRIBUTOS ------------------------------------------ #
# ------------------------------------------------------------------------- #
class ModeloProductoAtributoSerializer(serializers.Serializer):
    id_modelo_producto = serializers.IntegerField()
    id_empresa         = serializers.IntegerField()
    atributo_id        = serializers.IntegerField()
    nombre_atributo    = serializers.CharField()


# ------------------------------------------------------------------------- #
#  ★ NUEVO SERIALIZER → ATRIBUTO (CRUD)                                     #
# ------------------------------------------------------------------------- #
class AtributoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Atributo
        fields = ["id", "id_empresa", "id_modelo_producto", "nombre_atributo"]


# ------------------------------------------------------------------------- #
#  ★★★ NUEVO SERIALIZER → ORDEN COMPRA (LIST)                               #
# ------------------------------------------------------------------------- #
class OrdenCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrdenCompra
        fields = "__all__"


# ------------------------------------------------------------------------- #
#  ★★★ NUEVO SERIALIZER → SOLICITUD COMPRA (LIST)                           #
# ------------------------------------------------------------------------- #
class SolicitudCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SolicitudCompra
        fields = "__all__"


# ------------------------------------------------------------------------- #
#  ★★★ NUEVO SERIALIZER → SOLICITUD COMPRA (JOIN COMPLETO)                  #
# ------------------------------------------------------------------------- #
class SolicitudCompraJoinSerializer(serializers.Serializer):
    id                         = serializers.IntegerField()
    id_empresa                 = serializers.IntegerField()
    operador                   = serializers.CharField()
    id_aprobador               = serializers.IntegerField()
    estado_solicitud_compra    = serializers.CharField()
    fecha_registro             = serializers.DateTimeField()
    descripcion                = serializers.CharField()
    fecha_solicitud_compra     = serializers.DateTimeField(allow_null=True)
    tipo_solicitud             = serializers.CharField()
    titulo                     = serializers.CharField(allow_null=True)
    ruta_file                  = serializers.CharField(allow_null=True)
    cod_presupuesto            = serializers.CharField(allow_null=True)
    id_punto_venta             = serializers.IntegerField(allow_null=True)
    operador_rechazo           = serializers.IntegerField(allow_null=True)
    fecha_rechazo              = serializers.DateTimeField(allow_null=True)
    motivo_rechazo             = serializers.CharField(allow_null=True)
    id_requerimiento           = serializers.IntegerField(allow_null=True)


# ------------------------------------------------------------------------- #
#  ★★★ NUEVO SERIALIZER → COTIZACIONES POR SOLICITUD (JOIN COMPLETO)        #
# ------------------------------------------------------------------------- #
class CotizacionJoinSerializer(serializers.Serializer):
    id                   = serializers.IntegerField()
    id_empresa           = serializers.IntegerField()
    proveedor            = serializers.CharField()
    id_solicitud_compra  = serializers.IntegerField()
    fecha_cotizacion     = serializers.DateTimeField()
    total                = serializers.FloatField()
    validez_cotizacion   = serializers.IntegerField()
    archivo              = serializers.CharField(allow_null=True)
    estado_cotizacion    = serializers.IntegerField(allow_null=True)
    estado_detalle       = serializers.IntegerField(allow_null=True)
    iva                  = serializers.IntegerField(allow_null=True)
    folio                = serializers.CharField(allow_null=True)
    operador             = serializers.CharField()
    id_tipo_moneda       = serializers.IntegerField(allow_null=True)
