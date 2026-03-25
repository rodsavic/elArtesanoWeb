from django.utils import timezone

from apps.inventario.models import MovimientoProducto


def registrar_movimiento_producto(
    *,
    producto,
    tipo_movimiento,
    cantidad,
    usuario_id=None,
    referencia='',
    observacion='',
    fecha_movimiento=None,
):
    cantidad = int(cantidad or 0)
    if cantidad <= 0:
        raise ValueError('La cantidad del movimiento debe ser mayor a cero.')

    stock_anterior = int(producto.stock_actual or 0)
    if tipo_movimiento == MovimientoProducto.TIPO_ENTRADA:
        stock_posterior = stock_anterior + cantidad
    elif tipo_movimiento == MovimientoProducto.TIPO_SALIDA:
        if cantidad > stock_anterior:
            raise ValueError(
                f'Stock insuficiente para {producto.nombre}. Disponible: {stock_anterior}, solicitado: {cantidad}.'
            )
        stock_posterior = stock_anterior - cantidad
    else:
        raise ValueError('Tipo de movimiento no valido.')

    producto.stock_actual = stock_posterior
    producto.save(update_fields=['stock_actual'])

    return MovimientoProducto.objects.create(
        producto=producto,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_posterior=stock_posterior,
        fecha_movimiento=fecha_movimiento or timezone.now(),
        referencia=referencia,
        observacion=observacion,
        usuario_creacion=usuario_id,
    )
