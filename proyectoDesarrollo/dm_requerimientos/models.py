# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Documento(models.Model):
    id_empresa = models.IntegerField()
    id_requerimiento = models.ForeignKey('Requerimientos', models.DO_NOTHING, db_column='id_requerimiento')
    nombre = models.CharField(max_length=60)
    path = models.CharField(max_length=100)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."documento"'


class Requerimientos(models.Model):
    id_empresa = models.IntegerField()
    id_requerimientos_elementos = models.ForeignKey('RequerimientosElementos', models.DO_NOTHING, db_column='id_requerimientos_elementos')
    id_requerimientos_tipos = models.ForeignKey('RequerimientosTipos', models.DO_NOTHING, db_column='id_requerimientos_tipos')
    id_operador_origen = models.IntegerField()
    id_operador_asignado = models.IntegerField()
    id_operador_cierre = models.IntegerField()
    id_grupo_origen = models.IntegerField()
    id_grupo_actual = models.IntegerField()
    id_requerimientos_estados = models.ForeignKey('RequerimientosEstados', models.DO_NOTHING, db_column='id_requerimientos_estados', blank=True, null=True)
    id_cliente = models.IntegerField(blank=True, null=True)
    id_contrato = models.IntegerField(blank=True, null=True)
    id_suscriptor_producto_bodega = models.IntegerField(blank=True, null=True)
    solucion_en_linea = models.IntegerField()
    tipo_requerimiento = models.CharField(max_length=15)
    descripcion = models.TextField(blank=True, null=True)
    actividad = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    fecha_ultima_modificacion = models.DateTimeField(blank=True, null=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    prioridad = models.IntegerField(blank=True, null=True)
    numero_correos_enviados = models.CharField(max_length=6, blank=True, null=True)
    fecha_envio_ultimo_correo = models.DateTimeField(blank=True, null=True)
    nivel_requerimiento = models.CharField(max_length=100, blank=True, null=True)
    confirmar_lectura = models.IntegerField()
    fecha_confirma_lectura = models.DateTimeField(blank=True, null=True)
    id_punto_venta = models.IntegerField()
    hh = models.FloatField(blank=True, null=True)
    hh_cobro = models.FloatField(blank=True, null=True)
    fecha_agenda = models.DateField(blank=True, null=True)
    id_ejecutivo = models.IntegerField()
    id_ejecutivo_retiro = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos"'


class RequerimientosAsignacion(models.Model):
    id_empresa = models.IntegerField()
    id_requerimiento = models.ForeignKey(Requerimientos, models.DO_NOTHING, db_column='id_requerimiento')
    id_grupo = models.IntegerField()
    inicio_asignacion = models.DateTimeField()
    fin_asignacion = models.DateTimeField(blank=True, null=True)
    id_requerimientos_estados = models.ForeignKey('RequerimientosEstados', models.DO_NOTHING, db_column='id_requerimientos_estados')

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos_asignacion"'


class RequerimientosDetalle(models.Model):
    id_empresa = models.IntegerField()
    id_requerimiento = models.ForeignKey(Requerimientos, models.DO_NOTHING, db_column='id_requerimiento')
    tipo = models.CharField(max_length=255, blank=True, null=True)
    detalle = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos_detalle"'


class RequerimientosElementos(models.Model):
    id_empresa = models.IntegerField()
    id_requerimientos_tipos = models.ForeignKey('RequerimientosTipos', models.DO_NOTHING, db_column='id_requerimientos_tipos')
    etiqueta_elemento = models.CharField(max_length=255)
    envia_correo = models.IntegerField()
    asignable = models.IntegerField()
    modificable = models.IntegerField()
    requiere_documento = models.IntegerField()
    max_envio_correo = models.IntegerField()
    intervalo_envio_correo = models.IntegerField()
    boton_accion = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos_elementos"'


class RequerimientosEstados(models.Model):
    nombre_estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos_estados"'


class RequerimientosTipos(models.Model):
    id_empresa = models.IntegerField()
    id_grupo = models.IntegerField()
    etiqueta = models.CharField(max_length=255)
    asignable = models.IntegerField()
    modificable = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."requerimientos_tipos"'


class Sla(models.Model):
    id_empresa = models.IntegerField()
    id_requerimientos_estados = models.ForeignKey(RequerimientosEstados, models.DO_NOTHING, db_column='id_requerimientos_estados')
    id_operador1 = models.IntegerField(blank=True, null=True)
    tiempo_limite1 = models.IntegerField(blank=True, null=True)
    color1 = models.CharField(max_length=7, blank=True, null=True)
    id_operador2 = models.IntegerField(blank=True, null=True)
    tiempo_limite2 = models.IntegerField(blank=True, null=True)
    color2 = models.CharField(max_length=7, blank=True, null=True)
    id_operador3 = models.IntegerField(blank=True, null=True)
    tiempo_limite3 = models.IntegerField(blank=True, null=True)
    color3 = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_requerimientos"."sla"'
