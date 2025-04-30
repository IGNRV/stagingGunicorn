from rest_framework import serializers
from dm_logistica.models import ModeloProducto


class ModeloProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloProducto
        fields = [
            'id_modelo_producto',
            'id_empresa',
            'id_tipo_marca_producto',
            'id_identificador_serie',
            'id_unidad_medida',
            'codigo_interno',
            'fccid',
            'sku',
            'sku_codigo',
            'nombre_modelo',
            'descripcion',
            'imagen',
            'estado',
            'producto_seriado',
            'nombre_comercial',
            'despacho_express',
            'rebaja_consumo',
            'dias_rebaja_consumo',
            'orden_solicitud_despacho',
        ]