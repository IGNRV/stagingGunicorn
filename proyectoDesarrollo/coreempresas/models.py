from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

# Definir primero el arreglo de choices:
TIPO_TELEFONO_CHOICES = [
    ('FIJO', 'Fijo'),
    ('MOVIL', 'Móvil'),
    ('FAX', 'Fax'),
    ('OTRO', 'Otro'),
]

class Empresa(models.Model):
    razon_social = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    comuna = models.CharField(max_length=50, null=True, blank=True)
    ciudad = models.CharField(max_length=50, null=True, blank=True)
    rut = models.CharField(max_length=20, null=True, blank=True)
    giro = models.CharField(max_length=255, null=True, blank=True)
    acteco = models.CharField(max_length=10, null=True, blank=True)
    rut_firma = models.CharField(max_length=20, null=True, blank=True)
    logo = models.CharField(max_length=50, null=True, blank=True)
    subdominio = models.CharField(max_length=50, null=True, blank=True)
    titulo = models.CharField(max_length=50, null=True, blank=True)
    estado = models.IntegerField(default=1)
    fecha_incorporacion = models.DateTimeField(default=timezone.now)
    master = models.BooleanField(default=False)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    licencias = models.IntegerField(default=5)
    logo_grande = models.CharField(max_length=255, null=True, blank=True)
    ingreso_pcd = models.IntegerField()
    ingreso_funnel = models.IntegerField(default=0)
    mercado = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa"'
        indexes = [
            models.Index(fields=['mercado'], name='idx_empresa_mercado'),
            models.Index(fields=['estado'], name='idx_empresa_estado'),
        ]

    def __str__(self):
        return self.razon_social or ''


class EmpresaTelefono(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='telefonos')
    numero = models.CharField(max_length=20)
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_TELEFONO_CHOICES,  # Ahora sí existe
        validators=[RegexValidator(regex=r'^(FIJO|MOVIL|FAX|OTRO)$')],
    )
    principal = models.BooleanField(default=False)

    class Meta:
        db_table = '"dm_sistema"."empresa_telefono"'

    def __str__(self):
        return f'{self.empresa} - {self.numero}'


class EmpresaResolucion(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='resoluciones')
    numero = models.CharField(max_length=50)
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, default='SII')
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa_resolucion"'

    def __str__(self):
        return f'{self.empresa} - {self.numero}'


class EmpresaParam(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='parametros')
    campo = models.CharField(max_length=255, null=True, blank=True)
    valor = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa_param"'
        indexes = [
            models.Index(fields=['empresa'], name='idx_empresa_param_empresa_id'),
            models.Index(fields=['campo'], name='idx_empresa_param_campo'),
        ]

    def __str__(self):
        return f'{self.empresa} - {self.campo}'


class Grupo(models.Model):
    nombre = models.CharField(max_length=255, null=True, blank=True)
    asignable = models.IntegerField(default=1)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name='grupos')

    class Meta:
        db_table = '"dm_sistema"."grupo"'

    def __str__(self):
        return self.nombre or ''
