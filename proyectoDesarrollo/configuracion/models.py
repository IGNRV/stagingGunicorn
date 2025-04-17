from django.db import models
from coreempresas.models import Empresa   # <‑‑ Empresa real

# ---------------------------------------------------------------------
#  MODELO  : Modulo
# ---------------------------------------------------------------------
class Modulo(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_modulo')
    modulo      = models.CharField(max_length=50)
    nombre      = models.CharField(max_length=255)
    nombre_menu = models.CharField(max_length=100, null=True, blank=True)
    estado      = models.SmallIntegerField(null=True, blank=True)
    icon        = models.CharField(max_length=255, null=True, blank=True)
    orden       = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."modulos"'

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------
#  MODELO  : Menu
# ---------------------------------------------------------------------
class Menu(models.Model):
    id            = models.AutoField(primary_key=True, db_column='id_menu')
    url           = models.CharField(max_length=50)
    texto         = models.CharField(max_length=50, default='')
    etiqueta      = models.CharField(max_length=50, null=True, blank=True)
    descripcion   = models.CharField(max_length=255)
    nivel_menu    = models.IntegerField(default=3)
    orden         = models.IntegerField(null=True, blank=True)
    modificable   = models.CharField(max_length=2, default='SI')
    id_modulo     = models.ForeignKey(Modulo, on_delete=models.RESTRICT, null=True, blank=True, related_name='menus', db_column='id_modulo')
    separador_up  = models.IntegerField(default=0)

    class Meta:
        db_table = '"dm_sistema"."menus"'
        indexes  = [
            models.Index(fields=['id_modulo'], name='idx_modulo_menu'),
        ]

    def __str__(self):
        return self.descripcion


# ---------------------------------------------------------------------
#  MODELO  : EmpresaModulo
# ---------------------------------------------------------------------
class EmpresaModulo(models.Model):
    id         = models.AutoField(primary_key=True, db_column='id_empresa_modulo')
    id_empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='empresa_modulos', null=True, blank=True, db_column='id_empresa')
    id_modulo  = models.ForeignKey(Modulo,  on_delete=models.RESTRICT, related_name='empresa_modulos', null=True, blank=True, db_column='id_modulo')
    estado     = models.IntegerField(default=1)

    class Meta:
        db_table = '"dm_sistema"."empresa_modulos"'
        indexes  = [
            models.Index(fields=['id_empresa'], name='idx_empresa_emm'),
            models.Index(fields=['id_modulo'],  name='idx_mod_emm'),
        ]

    def __str__(self):
        return f'{self.id_empresa} - {self.id_modulo}'


# ---------------------------------------------------------------------
#  MODELO  : EmpresaModuloMenu
# ---------------------------------------------------------------------
class EmpresaModuloMenu(models.Model):
    id                = models.AutoField(primary_key=True, db_column='id_empresa_modulo_menu')
    id_empresa_modulo = models.ForeignKey(EmpresaModulo, on_delete=models.RESTRICT, related_name='empresa_modulos_menus', db_column='id_empresa_modulo')
    id_menu           = models.ForeignKey(Menu,          on_delete=models.RESTRICT, related_name='empresa_modulos_menus', db_column='id_menu')

    class Meta:
        db_table = '"dm_sistema"."empresa_modulos_menu"'
        indexes  = [
            models.Index(fields=['id_empresa_modulo'], name='idx_emp_mod_menu'),
            models.Index(fields=['id_menu'],           name='idx_menu_emm'),
        ]

    def __str__(self):
        return f'{self.id_empresa_modulo} - {self.id_menu}'
