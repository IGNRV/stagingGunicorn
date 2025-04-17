from django.db import models
from django.utils import timezone

from coreempresas.models  import Grupo, Empresa
from configuracion.models import EmpresaModulo, EmpresaModuloMenu

# ---------------------------------------------------------------------
#  MODELO  : Operador
# ---------------------------------------------------------------------
class Operador(models.Model):
    id                   = models.AutoField(primary_key=True, db_column='id_operador')
    username             = models.CharField(max_length=50)
    password             = models.CharField(max_length=80, default='')
    clear                = models.CharField(max_length=80,  null=True, blank=True)
    rut                  = models.CharField(max_length=15,  null=True, blank=True)
    nombres              = models.CharField(max_length=100, null=True, blank=True)
    apellido_paterno     = models.CharField(max_length=100, null=True, blank=True)
    apellido_materno     = models.CharField(max_length=100, null=True, blank=True)
    modificable          = models.IntegerField(default=1)
    email                = models.CharField(max_length=50,  null=True, blank=True)
    estado               = models.IntegerField(default=1)
    acceso_web           = models.IntegerField(default=0)
    conexion_fallida     = models.IntegerField(default=0)
    operador_administrador = models.CharField(max_length=50, default='0')
    id_grupo             = models.ForeignKey(Grupo,   on_delete=models.RESTRICT, null=True, blank=True, related_name='operadores', db_column='id_grupo')
    id_empresa           = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='operadores', db_column='id_empresa')
    superadmin           = models.IntegerField(default=0)
    fecha_creacion       = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"dm_sistema"."operador"'
        indexes  = [
            models.Index(fields=['id_empresa'], name='idx_opr_emp_id'),
            models.Index(fields=['id_grupo'],   name='idx_opr_grp_id'),
        ]

    def __str__(self):
        return self.username


# ---------------------------------------------------------------------
#  MODELO  : OperadorBodega
# ---------------------------------------------------------------------
class OperadorBodega(models.Model):
    id           = models.AutoField(primary_key=True, db_column='id_operador_bodega')
    id_operador  = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='bodegas', db_column='id_operador')
    id_bodega    = models.IntegerField()
    id_empresa   = models.ForeignKey(Empresa,  on_delete=models.RESTRICT, related_name='operador_bodegas', db_column='id_empresa')

    class Meta:
        db_table = '"dm_sistema"."operador_bodega"'
        indexes  = [
            models.Index(fields=['id_bodega'],  name='idx_opbdg_bdg_id'),
            models.Index(fields=['id_empresa'], name='idx_opbdg_emp_id'),
            models.Index(fields=['id_operador'], name='idx_opbdg_opr_id'),
        ]

    def __str__(self):
        return f'{self.id_operador} - Bodega {self.id_bodega}'


# ---------------------------------------------------------------------
#  MODELO  : OperadorEmpresaModulo
# ---------------------------------------------------------------------
class OperadorEmpresaModulo(models.Model):
    id                = models.AutoField(primary_key=True, db_column='id_operador_empresa_modulo')
    id_operador       = models.ForeignKey(Operador,      on_delete=models.RESTRICT, related_name='operador_empresa_modulos', db_column='id_operador')
    id_empresa_modulo = models.ForeignKey(EmpresaModulo, on_delete=models.RESTRICT, related_name='operador_empresa_modulos', db_column='id_empresa_modulo')

    class Meta:
        db_table = '"dm_sistema"."operador_empresa_modulos"'
        indexes  = [
            models.Index(fields=['id_operador'],       name='idx_oem_opr_id'),
            models.Index(fields=['id_empresa_modulo'], name='idx_oem_em_id'),
        ]

    def __str__(self):
        return f'{self.id_operador} - {self.id_empresa_modulo}'


# ---------------------------------------------------------------------
#  MODELO  : OperadorEmpresaModuloMenu
# ---------------------------------------------------------------------
class OperadorEmpresaModuloMenu(models.Model):
    id                     = models.AutoField(primary_key=True, db_column='id_operador_empresa_modulo_menu')
    id_operador            = models.ForeignKey(Operador,           on_delete=models.RESTRICT, related_name='operador_empresa_modulos_menus', db_column='id_operador')
    id_empresa_modulo_menu = models.ForeignKey(EmpresaModuloMenu,  on_delete=models.RESTRICT, related_name='operador_empresa_modulos_menus', db_column='id_empresa_modulo_menu')

    class Meta:
        db_table = '"dm_sistema"."operador_empresa_modulos_menu"'
        indexes  = [
            models.Index(fields=['id_operador'],            name='idx_oemm_opr_id'),
            models.Index(fields=['id_empresa_modulo_menu'], name='idx_oemm_mm_id'),
        ]

    def __str__(self):
        return f'{self.id_operador} - {self.id_empresa_modulo_menu}'


# ---------------------------------------------------------------------
#  MODELO  : OperadorGrupo
# ---------------------------------------------------------------------
class OperadorGrupo(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_operador_grupo')
    id_operador = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='operadores_grupo', db_column='id_operador')
    id_grupo    = models.ForeignKey(Grupo,    on_delete=models.RESTRICT, related_name='operadores_grupo', db_column='id_grupo')

    class Meta:
        db_table = '"dm_sistema"."operador_grupos"'
        indexes  = [
            models.Index(fields=['id_operador'], name='idx_opgr_opr_id'),
            models.Index(fields=['id_grupo'],    name='idx_opgr_grp_id'),
        ]

    def __str__(self):
        return f'{self.id_operador} - {self.id_grupo}'


# ---------------------------------------------------------------------
#  MODELO  : OperadorPuntoVenta
# ---------------------------------------------------------------------
class OperadorPuntoVenta(models.Model):
    id           = models.AutoField(primary_key=True, db_column='id_operador_punto_venta')
    id_operador  = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='operador_puntos_venta', db_column='id_operador')
    id_punto_venta = models.IntegerField()
    id_empresa   = models.ForeignKey(Empresa,  on_delete=models.RESTRICT, related_name='operador_puntos_ventas', db_column='id_empresa')

    class Meta:
        db_table = '"dm_sistema"."operador_punto_venta"'
        indexes  = [
            models.Index(fields=['id_empresa'],     name='idx_opv_emp_id'),
            models.Index(fields=['id_punto_venta'], name='idx_opv_pv_id'),
            models.Index(fields=['id_operador'],    name='idx_opv_opr_id'),
        ]

    def __str__(self):
        return f'{self.id_operador} - Punto de Venta {self.id_punto_venta}'


# ---------------------------------------------------------------------
#  MODELO  : Sesion
# ---------------------------------------------------------------------
class Sesion(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_sesion')
    ip          = models.CharField(max_length=20)
    fecha       = models.DateTimeField()
    id_operador = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='sesion', db_column='id_operador')
    id_empresa  = models.ForeignKey(Empresa,  on_delete=models.RESTRICT, null=True, blank=True, db_column='id_empresa')

    class Meta:
        db_table = '"dm_sistema"."sesiones"'
        indexes  = [
            models.Index(fields=['id_empresa'],  name='idx_ses_emp_id'),
            models.Index(fields=['id_operador'], name='idx_ses_opr_id'),
        ]

    def __str__(self):
        return f'Sesion {self.id} - {self.ip}'


# ---------------------------------------------------------------------
#  MODELO  : SesionActiva
# ---------------------------------------------------------------------
class SesionActiva(models.Model):
    id            = models.AutoField(primary_key=True, db_column='id_sesion_activa')
    id_empresa    = models.ForeignKey(Empresa,  on_delete=models.RESTRICT, null=True, blank=True, db_column='id_empresa')
    id_operador   = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='sesion_activa', db_column='id_operador')
    id_sesion     = models.ForeignKey(Sesion,   on_delete=models.RESTRICT, related_name='sesion_activa', db_column='id_sesion')
    fecha_registro = models.DateTimeField(default=timezone.now)

    token          = models.CharField(max_length=255, null=True, blank=True)
    cod_verificacion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."sesiones_activas"'
        indexes  = [
            models.Index(fields=['id_sesion'],   name='idx_sact_sid'),
            models.Index(fields=['id_empresa'],  name='idx_sact_emp_id'),
            models.Index(fields=['id_operador'], name='idx_sact_opr_id'),
        ]

    def __str__(self):
        return f'Sesion Activa {self.id}'
