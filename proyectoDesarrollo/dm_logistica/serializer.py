# dm_logistica/serializer.py
from __future__ import annotations

import os
from uuid import uuid4

from django.core.files.storage import default_storage
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from dm_logistica.models import ModeloProducto


def _save_uploaded_file(file_obj) -> str:
    """
    Guarda la imagen en el `default_storage` y devuelve la ruta/URL
    que quedará persistida en el campo `imagen` del modelo.
    """
    # carpeta por año/mes para mejor organización
    today_path = now().strftime("%Y/%m")
    # nombre único para evitar colisiones
    filename = f"{uuid4().hex}{os.path.splitext(file_obj.name)[1]}"
    full_path = os.path.join("modelo_producto", today_path, filename)
    saved_path = default_storage.save(full_path, file_obj)

    # Si el storage implementa `url`, devolvemos la URL; si no, la ruta
    return (
        default_storage.url(saved_path)
        if hasattr(default_storage, "url")
        else saved_path
    )


class ModeloProductoSerializer(serializers.ModelSerializer):
    # ← Campo virtual SOLO para escritura (el front enviará aquí el file)
    imagen_file = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model  = ModeloProducto
        fields = [
            # ------------------------ PK compuesta --------------------- #
            "id_modelo_producto",
            "id_empresa",
            # ------------------------ FK ------------------------------- #
            "id_tipo_marca_producto",
            "id_identificador_serie",
            "id_unidad_medida",
            # ------------------------ DATOS ---------------------------- #
            "codigo_interno",
            "sku",
            "sku_codigo",
            "nombre_modelo",
            "descripcion",
            # El campo real en BD sigue siendo `CharField`
            "imagen",
            "estado",
            "producto_seriado",
            "nombre_comercial",
            "despacho_express",
            "rebaja_consumo",
            "dias_rebaja_consumo",
            "orden_solicitud_despacho",
            # ------------------------ FILE ----------------------------- #
            "imagen_file",
        ]

        # Eliminamos la validación automática de unicidad sobre
        # `id_modelo_producto` para no chocar con la PK compuesta.
        extra_kwargs = {
            "id_modelo_producto": {"validators": []},
            # El campo `imagen` solo se lee; la subida real
            # la manejamos con `imagen_file`.
            "imagen": {"read_only": True},
        }

        # Validación de unicidad compuesta
        validators = [
            UniqueTogetherValidator(
                queryset=ModeloProducto.objects.all(),
                fields=["id_modelo_producto", "id_empresa"],
                message=(
                    "Ya existe modelo producto con esta combinación de "
                    "id_modelo_producto e id_empresa."
                ),
            )
        ]

    # --------------------------- CREATE --------------------------- #
    def create(self, validated_data):
        imagen_subida = validated_data.pop("imagen_file", None)
        if imagen_subida:
            validated_data["imagen"] = _save_uploaded_file(imagen_subida)
        return super().create(validated_data)

    # --------------------------- UPDATE --------------------------- #
    def update(self, instance, validated_data):
        imagen_subida = validated_data.pop("imagen_file", None)
        if imagen_subida:
            validated_data["imagen"] = _save_uploaded_file(imagen_subida)
        return super().update(instance, validated_data)
