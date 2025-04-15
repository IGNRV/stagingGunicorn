from django.db import models
# <<-- Corrección: Importar la clase Empresa de la app coreempresas
from coreempresas.models import Empresa

# Create your models here.
class Modulo(models.Model):
    modulo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    nombre_menu = models.CharField(max_length=100, null=True, blank=True)
    estado = models.SmallIntegerField(null=True, blank=True)
    icon = models.CharField(max_length=255, null=True, blank=True)
    orden = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."modulos"'

    def __str__(self):
        return self.nombre

class Menu(models.Model):
    url = models.CharField(max_length=50)
    texto = models.CharField(max_length=50, default='')
    etiqueta = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=255)
    nivel_menu = models.IntegerField(default=3)
    orden = models.IntegerField(null=True, blank=True)
    modificable = models.CharField(max_length=2, default='SI')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, null=True, blank=True, related_name='menus')
    separador_up = models.IntegerField(default=0)

    class Meta:
        db_table = '"dm_sistema"."menus"'

    def __str__(self):
        return self.descripcion

class EmpresaModulo(models.Model):
    # Ahora Empresa está definido porque lo importamos de coreempresas.models
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='empresa_modulos')
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='empresa_modulos')
    estado = models.IntegerField(default=1)

    class Meta:
        db_table = '"dm_sistema"."empresa_modulos"'

    def __str__(self):
        return f'{self.empresa} - {self.modulo}'

class EmpresaModuloMenu(models.Model):
    empresa_modulo = models.ForeignKey(EmpresaModulo, on_delete=models.CASCADE, related_name='menus')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='empresa_modulos_menus')

    class Meta:
        db_table = '"dm_sistema"."empresa_modulos_menu"'

    def __str__(self):
        return f'{self.empresa_modulo} - {self.menu}'
