# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class TipoMoneda(models.Model):
    simbolo = models.CharField(max_length=10, blank=True, null=True, db_comment='SIMBOLO DE MONEDA')
    descripcion = models.CharField(max_length=50, blank=True, null=True, db_comment='DESCRIPCION DEL TIPO DE MONEDA')
    requiere_conversion = models.SmallIntegerField(db_comment='indica si requiere factor para convertir a pesos 0=no 1=si')
    requiere_fecha = models.SmallIntegerField(db_comment='indica si el tipo moneda se debe validar por fecha o solo es necesario obtener el ultimo ingresado 0=no 1=si')

    class Meta:
        managed = False
        db_table = '"dm_catalogo"."tipo_moneda"'


class TipoMonedaValores(models.Model):
    id_tipo_moneda = models.ForeignKey(TipoMoneda, models.DO_NOTHING, db_column='id_tipo_moneda', db_comment='IDENTIFICA UN TIPO DE MONEDA')
    fecha = models.DateField(db_comment='FECHA PARA APLICAR EL VALOR')
    valor = models.FloatField(blank=True, null=True, db_comment='VALOR PARA EL TIPO DE MONEDA')

    class Meta:
        managed = False
        db_table = '"dm_catalogo"."tipo_moneda_valores"'
