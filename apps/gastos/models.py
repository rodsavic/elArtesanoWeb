from django.db import models
from django.utils import timezone


class Gasto(models.Model):
    id_gasto = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150, null=False, blank=False)
    monto = models.DecimalField(max_digits=12, decimal_places=2, null=False)
    fecha_gasto = models.DateField(default=timezone.localdate)
    usuario_creacion = models.IntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gastos'
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha_gasto', '-id_gasto']

    def __str__(self):
        return f'{self.nombre} - {self.monto}'
