from django.db import models
from django.utils import timezone

from apps.productos.models import Producto


class MovimientoProducto(models.Model):
    TIPO_ENTRADA = 'ENTRADA'
    TIPO_SALIDA = 'SALIDA'
    TIPOS_MOVIMIENTO = (
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SALIDA, 'Salida'),
    )

    id_movimiento = models.BigAutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=10, choices=TIPOS_MOVIMIENTO)
    cantidad = models.IntegerField(default=0)
    stock_anterior = models.IntegerField(default=0)
    stock_posterior = models.IntegerField(default=0)
    fecha_movimiento = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=100, blank=True, default='')
    observacion = models.TextField(blank=True, default='')
    usuario_creacion = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'movimiento_producto'
        verbose_name = 'Movimiento de producto'
        verbose_name_plural = 'Movimientos de productos'
        ordering = ['-fecha_movimiento', '-id_movimiento']

    def __str__(self):
        return f'{self.producto.nombre} - {self.tipo_movimiento} - {self.cantidad}'
