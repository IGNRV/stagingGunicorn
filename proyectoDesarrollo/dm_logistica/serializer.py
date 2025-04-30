# dm_logistica/serializer.py

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
        # Quitamos el validador único por sí solo sobre id_modelo_producto
        extra_kwargs = {
            'id_modelo_producto': {'validators': []},
        }
        # Añadimos validación de unicidad compuesta
        validators = [
            UniqueTogetherValidator(
                queryset=ModeloProducto.objects.all(),
                fields=['id_modelo_producto', 'id_empresa'],
                message="Ya existe modelo producto con esta combinación de id_modelo_producto e id_empresa."
            )
        ]
