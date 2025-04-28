# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Empresa(models.Model):
    razon_social = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    comuna = models.CharField(max_length=50, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    rut = models.CharField(max_length=20, blank=True, null=True)
    giro = models.CharField(max_length=255, blank=True, null=True)
    acteco = models.CharField(max_length=10, blank=True, null=True)
    rut_firma = models.CharField(max_length=20, blank=True, null=True)
    logo = models.CharField(max_length=50, blank=True, null=True)
    subdominio = models.CharField(max_length=50, blank=True, null=True)
    titulo = models.CharField(max_length=50, blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    fecha_incorporacion = models.DateTimeField(blank=True, null=True)
    master = models.BooleanField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    licencias = models.IntegerField(blank=True, null=True)
    logo_grande = models.CharField(max_length=255, blank=True, null=True)
    ingreso_pcd = models.IntegerField()
    ingreso_funnel = models.IntegerField(blank=True, null=True)
    mercado = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa"'


class EmpresaModulo(models.Model):
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    id_modulo = models.ForeignKey('Modulos', models.DO_NOTHING, db_column='id_modulo')
    estado = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa_modulo"'


class EmpresaModulosMenu(models.Model):
    id_empresa_modulo = models.ForeignKey(EmpresaModulo, models.DO_NOTHING, db_column='id_empresa_modulo')
    id_menu = models.ForeignKey('Menus', models.DO_NOTHING, db_column='id_menu')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa_modulos_menu"'


class EmpresaParam(models.Model):
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    campo = models.CharField(max_length=255, blank=True, null=True)
    valor = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa_param"'


class EmpresaResolucion(models.Model):
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    numero = models.CharField(max_length=50)
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa_resolucion"'


class EmpresaTelefono(models.Model):
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    numero = models.CharField(max_length=20)
    tipo = models.CharField(max_length=10)
    principal = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."empresa_telefono"'


class Grupo(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    asignable = models.IntegerField(blank=True, null=True)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."grupo"'


class Log(models.Model):
    id_operador = models.ForeignKey('Operador', models.DO_NOTHING, db_column='id_operador')
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    operacion = models.CharField(max_length=30)
    detalle = models.TextField()
    script = models.CharField(max_length=100)
    tabla = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    id_cliente = models.IntegerField(blank=True, null=True)
    id_contrato = models.IntegerField(blank=True, null=True)
    id_suscriptor = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."log"'


class Menus(models.Model):
    url = models.CharField(max_length=50)
    texto = models.CharField(max_length=50, blank=True, null=True)
    etiqueta = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255)
    nivel_menu = models.IntegerField(blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)
    modificable = models.CharField(max_length=2, blank=True, null=True)
    id_modulo = models.ForeignKey('Modulos', models.DO_NOTHING, db_column='id_modulo')
    separador_up = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."menus"'


class Modulos(models.Model):
    modulo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    nombre_menu = models.CharField(max_length=100, blank=True, null=True)
    estado = models.SmallIntegerField(blank=True, null=True)
    icon = models.CharField(max_length=255, blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."modulos"'


class Operador(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=80, blank=True, null=True)
    clear = models.CharField(max_length=80, blank=True, null=True)
    rut = models.CharField(max_length=15, blank=True, null=True)
    nombres = models.CharField(max_length=100, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=100, blank=True, null=True)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    modificable = models.IntegerField(blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    acceso_web = models.IntegerField(blank=True, null=True)
    conexion_fallida = models.IntegerField(blank=True, null=True)
    operador_administrador = models.CharField(max_length=50, blank=True, null=True)
    id_grupo = models.ForeignKey(Grupo, models.DO_NOTHING, db_column='id_grupo')
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    superadmin = models.IntegerField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador"'


class OperadorBodega(models.Model):
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_bodega = models.IntegerField()
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador_bodega"'


class OperadorEmpresaModulos(models.Model):
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_empresa_modulo = models.ForeignKey(EmpresaModulo, models.DO_NOTHING, db_column='id_empresa_modulo')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador_empresa_modulos"'


class OperadorEmpresaModulosMenu(models.Model):
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_empresa_modulos_menu = models.ForeignKey(EmpresaModulosMenu, models.DO_NOTHING, db_column='id_empresa_modulos_menu')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador_empresa_modulos_menu"'


class OperadorGrupos(models.Model):
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_grupo = models.ForeignKey(Grupo, models.DO_NOTHING, db_column='id_grupo')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador_grupos"'


class OperadorPuntoVenta(models.Model):
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_punto_venta = models.IntegerField()
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."operador_punto_venta"'


class Sesiones(models.Model):
    ip = models.CharField(max_length=20)
    fecha = models.DateTimeField()
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')

    class Meta:
        managed = False
        db_table = '"dm_sistema"."sesiones"'


class SesionesActivas(models.Model):
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    id_operador = models.ForeignKey(Operador, models.DO_NOTHING, db_column='id_operador')
    id_sesion = models.ForeignKey(Sesiones, models.DO_NOTHING, db_column='id_sesion')
    fecha_registro = models.DateTimeField(blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    cod_verificacion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"dm_sistema"."sesiones_activas"'
