from django.db import models
# Importa Operador (y Empresa si usas este FK)
from operadores.models import Operador
from coreempresas.models import Empresa  # Si también usas Empresa en logs

class Log(models.Model):
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE, related_name='logs')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    operacion = models.CharField(max_length=30)
    detalle = models.TextField()
    script = models.CharField(max_length=100)
    tabla = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    cliente_id = models.IntegerField(default=0)
    contrato_id = models.IntegerField(default=0)
    suscriptor_id = models.IntegerField(default=0)

    class Meta:
        db_table = '"dm_sistema"."log"'
        indexes = [
            models.Index(fields=['cliente_id'], name='idx_log_cliente_id'),
            models.Index(fields=['contrato_id'], name='idx_log_contrato_id'),
            models.Index(fields=['empresa'], name='idx_log_empresa_id'),
        ]

    def __str__(self):
        return f'Log {self.id} - {self.operacion}'
