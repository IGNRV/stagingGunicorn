from django.db import models
from operadores.models import Operador
from coreempresas.models import Empresa

# ---------------------------------------------------------------------
#  MODELO  : Log
# ---------------------------------------------------------------------
class Log(models.Model):
    id            = models.AutoField(primary_key=True, db_column='id_log')
    id_operador   = models.ForeignKey(Operador, on_delete=models.RESTRICT, related_name='logs', db_column='id_operador')
    id_empresa    = models.ForeignKey(Empresa,  on_delete=models.RESTRICT, null=True, blank=True, db_column='id_empresa')
    operacion     = models.CharField(max_length=30)
    detalle       = models.TextField()
    script        = models.CharField(max_length=100)
    tabla         = models.CharField(max_length=100)
    fecha         = models.DateTimeField()
    id_cliente    = models.IntegerField(default=0)
    id_contrato   = models.IntegerField(default=0)
    id_suscriptor = models.IntegerField(default=0)

    class Meta:
        db_table = '"dm_sistema"."log"'
        indexes  = [
            models.Index(fields=['id_cliente'],   name='idx_log_idcliente'),
            models.Index(fields=['id_contrato'],  name='idx_log_idcontrato'),
            models.Index(fields=['id_empresa'],   name='idx_log_idemp'),
            models.Index(fields=['id_suscriptor'], name='idx_log_idsuscriptor'),
            models.Index(fields=['id_operador'], name='idx_log_idoperador'),
        ]

    def __str__(self):
        return f'Log {self.id} - {self.operacion}'
