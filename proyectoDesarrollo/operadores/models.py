from django.db import models
from django.utils import timezone
from coreempresas.models import Grupo, Empresa
from configuracion.models import EmpresaModulo, EmpresaModuloMenu

class Operador(models.Model):
    operador_id = models.CharField(max_length=50)
    password = models.CharField(max_length=80, default='')
    clear = models.CharField(max_length=80, null=True, blank=True)
    rut = models.CharField(max_length=15, null=True, blank=True)
    nombres = models.CharField(max_length=100, null=True, blank=True)
    apellido_paterno = models.CharField(max_length=100, null=True, blank=True)
    apellido_materno = models.CharField(max_length=100, null=True, blank=True)
    modificable = models.IntegerField(default=1)
    email = models.CharField(max_length=50, null=True, blank=True)
    estado = models.IntegerField(default=1)
    acceso_web = models.IntegerField(default=0)
    conexion_fallida = models.IntegerField(default=0)
    operador_administrador = models.CharField(max_length=50, default='0')
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='operadores'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='operadores'
    )
    superadmin = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"dm_sistema"."operador"'
        unique_together = (('operador_id', 'empresa'),)
        indexes = [
            models.Index(fields=['empresa'], name='idx_opr_emp_id'),
            models.Index(fields=['grupo'], name='idx_opr_grp_id'),
        ]

    def __str__(self):
        return self.operador_id


class OperadorBodega(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.CASCADE,
        related_name='bodegas'
    )
    bodega_id = models.IntegerField()
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='operador_bodegas'
    )

    class Meta:
        db_table = '"dm_sistema"."operador_bodega"'
        indexes = [
            models.Index(fields=['bodega_id'], name='idx_opbdg_bdg_id'),
            models.Index(fields=['empresa'], name='idx_opbdg_emp_id'),
        ]

    def __str__(self):
        return f'{self.operador} - Bodega {self.bodega_id}'


class OperadorEmpresaModulo(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.CASCADE,
        related_name='empresa_modulos'
    )
    empresa_modulo = models.ForeignKey(
        EmpresaModulo,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        db_table = '"dm_sistema"."operador_empresa_modulos"'
        indexes = [
            models.Index(fields=['operador'], name='idx_oem_opr_id'),
            models.Index(fields=['empresa_modulo'], name='idx_oem_em_id'),
        ]

    def __str__(self):
        return f'{self.operador} - {self.empresa_modulo}'


class OperadorEmpresaModuloMenu(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.CASCADE,
        related_name='empresa_modulos_menus'
    )
    empresa_modulo_menu = models.ForeignKey(
        EmpresaModuloMenu,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        db_table = '"dm_sistema"."operador_empresa_modulos_menu"'
        indexes = [
            models.Index(fields=['operador'], name='idx_oemm_opr_id'),
            models.Index(fields=['empresa_modulo_menu'], name='idx_oemm_mm_id'),
        ]

    def __str__(self):
        return f'{self.operador} - {self.empresa_modulo_menu}'


class OperadorGrupo(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.CASCADE,
        related_name='grupos_operador'
    )
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        related_name='operadores_grupo'
    )

    class Meta:
        db_table = '"dm_sistema"."operador_grupos"'
        unique_together = (('operador', 'grupo'),)

    def __str__(self):
        return f'{self.operador} - {self.grupo}'


class OperadorPuntoVenta(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.CASCADE,
        related_name='puntos_venta'
    )
    punto_venta_id = models.IntegerField()
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='operador_punto_ventas'
    )

    class Meta:
        db_table = '"dm_sistema"."operador_punto_venta"'
        indexes = [
            models.Index(fields=['empresa'], name='idx_opv_emp_id'),
        ]

    def __str__(self):
        return f'{self.operador} - Punto de Venta {self.punto_venta_id}'


class Sesion(models.Model):
    ip = models.CharField(max_length=20)
    fecha = models.DateTimeField()
    operador_id = models.CharField(max_length=50)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        db_table = '"dm_sistema"."sesiones"'

    def __str__(self):
        return f'Sesion {self.id} - {self.operador_id}'


class SesionActiva(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    operador_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    sesion_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    fecha_registro = models.DateTimeField(default=timezone.now)

    token = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    cod_verificacion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        db_table = '"dm_sistema"."sesiones_activas"'
        indexes = [
            models.Index(fields=['sesion_id'], name='idx_sact_sid'),
            models.Index(fields=['empresa'], name='idx_sact_emp_id'),
        ]

    def __str__(self):
        return f'Sesion Activa {self.id}'
