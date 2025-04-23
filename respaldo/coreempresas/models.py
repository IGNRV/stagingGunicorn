from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

# ---------------------------------------------------------------------
#  Choices
# ---------------------------------------------------------------------
TIPO_TELEFONO_CHOICES = [
    ('FIJO', 'Fijo'),
    ('MOVIL', 'Móvil'),
    ('FAX',  'Fax'),
    ('OTRO', 'Otro'),
]

# ---------------------------------------------------------------------
#  MODELO  : Empresa
# ---------------------------------------------------------------------
class Empresa(models.Model):
    id                 = models.AutoField(primary_key=True, db_column='id_empresa')
    razon_social       = models.CharField(max_length=100, null=True, blank=True)
    direccion          = models.CharField(max_length=200, null=True, blank=True)
    comuna             = models.CharField(max_length=50,  null=True, blank=True)
    ciudad             = models.CharField(max_length=50,  null=True, blank=True)
    rut                = models.CharField(max_length=20,  null=True, blank=True)
    giro               = models.CharField(max_length=255, null=True, blank=True)
    acteco             = models.CharField(max_length=10,  null=True, blank=True)
    rut_firma          = models.CharField(max_length=20,  null=True, blank=True)
    logo               = models.CharField(max_length=50,  null=True, blank=True)
    subdominio         = models.CharField(max_length=50,  null=True, blank=True)
    titulo             = models.CharField(max_length=50,  null=True, blank=True)
    estado             = models.IntegerField(default=1)
    fecha_incorporacion = models.DateTimeField(default=timezone.now)
    master             = models.BooleanField(default=False)
    fecha_modificacion = models.DateTimeField(null=True, blank=True)
    licencias          = models.IntegerField(default=5)
    logo_grande        = models.CharField(max_length=255, null=True, blank=True)
    ingreso_pcd        = models.IntegerField()
    ingreso_funnel     = models.IntegerField(default=0)
    mercado            = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa"'
        indexes  = [
            models.Index(fields=['mercado'],      name='idx_empresa_mercado'),
            models.Index(fields=['estado'],       name='idx_empresa_estado'),
            models.Index(fields=['ingreso_pcd'],  name='idx_emp_ing_pcd'),
        ]

    def __str__(self):
        return self.razon_social or ''


# ---------------------------------------------------------------------
#  MODELO  : EmpresaTelefono
# ---------------------------------------------------------------------
class EmpresaTelefono(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_empresa_telefono')
    id_empresa  = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='telefonos', db_column='id_empresa')
    numero      = models.CharField(max_length=20)
    tipo        = models.CharField(
        max_length=10,
        choices=TIPO_TELEFONO_CHOICES,
        validators=[RegexValidator(regex=r'^(FIJO|MOVIL|FAX|OTRO)$')],
    )
    principal   = models.BooleanField(default=False)

    class Meta:
        db_table = '"dm_sistema"."empresa_telefono"'
        indexes  = [
            models.Index(fields=['id_empresa', 'principal'], name='idx_empresa_telem_princ'),
        ]

    def __str__(self):
        return f'{self.id_empresa} - {self.numero}'


# ---------------------------------------------------------------------
#  MODELO  : EmpresaResolucion
# ---------------------------------------------------------------------
class EmpresaResolucion(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_empresa_resolucion')
    id_empresa  = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='resoluciones', db_column='id_empresa')
    numero      = models.CharField(max_length=50)
    fecha       = models.DateField()
    tipo        = models.CharField(max_length=20, default='SII')
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa_resolucion"'
        indexes  = [
            models.Index(fields=['id_empresa'], name='idx_emp_res_empid'),
            models.Index(fields=['numero'],     name='idx_emp_res_num'),
            models.Index(fields=['fecha'],      name='idx_emp_res_fecha'),
            models.Index(fields=['descripcion'], name='idx_emp_res_desc'),
        ]

    def __str__(self):
        return f'{self.id_empresa} - {self.numero}'


# ---------------------------------------------------------------------
#  MODELO  : EmpresaParam
# ---------------------------------------------------------------------
class EmpresaParam(models.Model):
    id         = models.AutoField(primary_key=True, db_column='id_empresa_param')
    id_empresa = models.ForeignKey(Empresa, on_delete=models.RESTRICT, related_name='parametros', db_column='id_empresa')
    campo      = models.CharField(max_length=255, null=True, blank=True)
    valor      = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = '"dm_sistema"."empresa_param"'
        indexes  = [
            models.Index(fields=['id_empresa'], name='idx_emp_par_emp_id'),
            models.Index(fields=['campo'],      name='idx_emp_par_campo'),
            models.Index(fields=['valor'],      name='idx_emp_par_valor'),
        ]

    def __str__(self):
        return f'{self.id_empresa} - {self.campo}'


# ---------------------------------------------------------------------
#  MODELO  : Grupo
# ---------------------------------------------------------------------
class Grupo(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id_grupo')
    nombre      = models.CharField(max_length=255, null=True, blank=True)
    asignable   = models.IntegerField(default=1)
    id_empresa  = models.ForeignKey(Empresa, on_delete=models.RESTRICT, null=True, blank=True, related_name='grupos', db_column='id_empresa')

    class Meta:
        db_table = '"dm_sistema"."grupo"'
        indexes  = [
            models.Index(fields=['id_empresa'], name='idx_grupo_emp_id'),
            models.Index(fields=['asignable'],  name='idx_grupo_asign'),
        ]

    def __str__(self):
        return self.nombre or ''
