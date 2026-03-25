import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.factura.models import Factura
from apps.inventario.models import MovimientoProducto
from apps.inventario.services import registrar_movimiento_producto
from apps.productos.models import Producto
from apps.tipo_pago.models import TipoPago
from apps.ventas.models import TipoVenta, Venta, VentaDetalle, VentaTipoDePago


def _tipos_de_venta_disponibles():
    return TipoVenta.objects.exclude(nombre__icontains='pedido')


def _registrar_formas_pago(venta, pagos):
    for tipo_pago_id, monto in pagos:
        monto = float(monto or 0)
        if monto <= 0:
            continue
        VentaTipoDePago.objects.create(
            id_venta=venta,
            id_tipo_pago=TipoPago.objects.get(id_tipo_pago=tipo_pago_id),
            monto=monto,
        )


def _registrar_detalles_y_stock(venta, productos_data, usuario_id):
    for detalle in productos_data:
        producto = Producto.objects.select_for_update().get(id_producto=detalle['id_producto'])
        cantidad_producto = int(float(detalle['cantidad']))
        precio_lista = float(detalle.get('precio_lista') or producto.precio_actual or 0)
        precio_unitario = float(detalle.get('precio_unitario') or precio_lista)
        total_detalle = float(detalle['total_detalle'])
        total_iva_10 = float(detalle['total_detalle_iva_10'])
        total_iva_5 = float(detalle['total_detalle_iva_5'])

        VentaDetalle.objects.create(
            id_venta=venta,
            id_producto=producto,
            cantidad_producto=cantidad_producto,
            precio_lista=precio_lista,
            precio_unitario=precio_unitario,
            total_detalle=total_detalle,
            total_iva_5=total_iva_5,
            total_iva_10=total_iva_10,
        )

        registrar_movimiento_producto(
            producto=producto,
            tipo_movimiento=MovimientoProducto.TIPO_SALIDA,
            cantidad=cantidad_producto,
            usuario_id=usuario_id,
            referencia=f'VENTA-{venta.id_venta}',
            observacion='Salida generada por venta.',
            fecha_movimiento=venta.fecha_venta,
        )


def _revertir_detalles_y_stock(detalles, usuario_id, referencia, observacion):
    for detalle in detalles.select_related('id_producto'):
        producto = Producto.objects.select_for_update().get(id_producto=detalle.id_producto_id)
        registrar_movimiento_producto(
            producto=producto,
            tipo_movimiento=MovimientoProducto.TIPO_ENTRADA,
            cantidad=int(float(detalle.cantidad_producto)),
            usuario_id=usuario_id,
            referencia=referencia,
            observacion=observacion,
            fecha_movimiento=timezone.now(),
        )


@login_required(login_url="/")
def ventasReadView(request, fecha=None):
    if fecha:
        fecha_venta = datetime.strptime(fecha, '%Y-%m-%d').date()
    else:
        fecha_venta = timezone.localdate()

    ventas = Venta.objects.filter(fecha_venta__date=fecha_venta).order_by('-fecha_venta')
    ids_ventas = ventas.values_list('id_venta', flat=True)
    pagos = VentaTipoDePago.objects.filter(id_venta__in=ids_ventas).select_related('id_tipo_pago')

    formas_pago_dict = {}
    total_efectivo = 0
    total_otros_medios = 0
    for pago in pagos:
        formas_pago_dict.setdefault(pago.id_venta_id, []).append(pago.id_tipo_pago.descripcion)
        if pago.id_tipo_pago.descripcion.lower() == 'efectivo':
            total_efectivo += float(pago.monto or 0)
        else:
            total_otros_medios += float(pago.monto or 0)

    facturas_emitidas = Factura.objects.filter(
        id_venta__in=ids_ventas,
        estado=Factura.ESTADO_EMITIDA
    ).select_related('id_venta')
    factura_por_venta = {factura.id_venta_id: factura for factura in facturas_emitidas}

    for venta in ventas:
        venta.formas_pago = ", ".join(formas_pago_dict.get(venta.id_venta, []))
        factura = factura_por_venta.get(venta.id_venta)
        venta.factura_emitida = factura is not None
        venta.id_factura_emitida = factura.id_factura if factura else None

    total_ventas = ventas.aggregate(total_ventas=Sum('total_venta'))['total_ventas'] or 0
    columnas = ['Cliente', 'Total', 'IVA 10', 'Forma de Pago', 'Tipo de Venta', 'Fecha']
    paginator = Paginator(ventas, 10)
    ventas_por_pagina = paginator.get_page(request.GET.get('page', 1))

    context = {
        'columnas': columnas,
        'ventas_por_pagina': ventas_por_pagina,
        'total_ventas': total_ventas,
        'total_efectivo': total_efectivo,
        'total_otros_medios': total_otros_medios,
        'fecha_venta': fecha_venta,
    }

    return render(request, 'ventas/ventas.html', context=context)


@login_required(login_url="/")
def ventasCreateView(request):
    productos = Producto.objects.all().order_by('nombre')
    clientes = Cliente.objects.all().order_by('id_cliente')
    tipos_de_pago = TipoPago.objects.all()
    tipo_venta = _tipos_de_venta_disponibles()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                total_iva_10 = request.POST['total_iva_10']
                total_iva_5 = request.POST['total_iva_5']
                id_cliente = request.POST['cliente']
                total_venta = request.POST['total_venta']
                pago_pos = float(request.POST.get('pos', 0) or 0)
                pago_efectivo = float(request.POST.get('efectivo', 0) or 0)
                pago_transferencia = float(request.POST.get('transferencia', 0) or 0)
                fecha_venta_str = request.POST.get('fecha_venta')
                id_tipo_venta = request.POST.get('tipo_venta')

                fecha_venta = (
                    datetime.strptime(fecha_venta_str, "%Y-%m-%dT%H:%M")
                    if fecha_venta_str else timezone.now()
                )
                tipo_venta_obj = TipoVenta.objects.filter(id=id_tipo_venta).first() if id_tipo_venta else None

                nueva_venta = Venta.objects.create(
                    fecha_venta=fecha_venta,
                    total_iva_10=total_iva_10,
                    total_iva_5=total_iva_5,
                    id_cliente=Cliente.objects.get(id_cliente=id_cliente),
                    total_venta=total_venta,
                    usuario_creacion=request.user.id,
                    id_tipo_venta=tipo_venta_obj,
                )

                productos_json = request.POST.get('productos_json')
                productos_data = json.loads(productos_json)
                _registrar_detalles_y_stock(nueva_venta, productos_data, request.user.id)

                _registrar_formas_pago(
                    nueva_venta,
                    [
                        (2, pago_pos),
                        (1, pago_efectivo),
                        (3, pago_transferencia),
                    ],
                )

            messages.success(request, "Venta registrada exitosamente")
            return redirect('ventas:ventas')
        except Exception as error:
            messages.error(request, f"Error al registrar venta: {error}")
            logging.error('Error al crear venta: %s', error)
            return redirect('ventas:crear_venta')

    context = {
        'productos': productos,
        'clientes': clientes,
        'cliente_default_id': clientes.first().id_cliente if clientes.exists() else None,
        'tipos_de_pago': tipos_de_pago,
        'now': timezone.now(),
        'tipo_venta': tipo_venta,
    }
    return render(request, 'ventas/crear_venta.html', context=context)


@login_required(login_url="/")
def ventasEditView(request, id_venta):
    venta = get_object_or_404(Venta, id_venta=id_venta)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                venta.total_iva_10 = request.POST['total_iva_10']
                venta.total_iva_5 = request.POST['total_iva_5']
                venta.id_cliente = Cliente.objects.get(id_cliente=request.POST['cliente'])
                venta.total_venta = request.POST['total_venta']
                venta.fecha_venta = (
                    datetime.strptime(request.POST.get('fecha_venta'), "%Y-%m-%dT%H:%M")
                    if request.POST.get('fecha_venta') else timezone.now()
                )
                venta.id_tipo_venta = TipoVenta.objects.filter(id=request.POST.get('tipo_venta')).first()
                venta.usuario_creacion = request.user.id
                venta.save()

                detalles_previos = VentaDetalle.objects.filter(id_venta=venta)
                _revertir_detalles_y_stock(
                    detalles_previos,
                    request.user.id,
                    referencia=f'VENTA-{venta.id_venta}-EDICION',
                    observacion='Reversion de stock por edicion de venta.',
                )
                detalles_previos.delete()

                productos_data = json.loads(request.POST.get('productos_json') or '[]')
                _registrar_detalles_y_stock(venta, productos_data, request.user.id)

                VentaTipoDePago.objects.filter(id_venta=venta).delete()
                _registrar_formas_pago(
                    venta,
                    [
                        (2, request.POST.get('pos', 0)),
                        (1, request.POST.get('efectivo', 0)),
                        (3, request.POST.get('transferencia', 0)),
                    ],
                )

            messages.success(request, 'Venta actualizada exitosamente.')
            return redirect('ventas:ventas')
        except Exception as error:
            messages.error(request, f"Error al actualizar venta: {error}")
            logging.error('Error al editar venta: %s', error)
            return redirect(reverse('ventas:editar_venta', args=[id_venta]))

    detalle_venta = VentaDetalle.objects.filter(id_venta=id_venta).select_related('id_producto')
    detalle_tipo_pago = VentaTipoDePago.objects.filter(id_venta=id_venta)
    monto_efectivo = 0
    monto_pos = 0
    monto_transferencia = 0

    for pago in detalle_tipo_pago:
        if pago.id_tipo_pago_id == 1:
            monto_efectivo = pago.monto
        elif pago.id_tipo_pago_id == 2:
            monto_pos = pago.monto
        elif pago.id_tipo_pago_id == 3:
            monto_transferencia = pago.monto

    detalles_serializados = []
    for detalle in detalle_venta:
        detalle.precio_unitario_venta = float(detalle.precio_unitario or 0)
        detalle.precio_lista_venta = float(detalle.precio_lista or detalle.id_producto.precio_actual or 0)
        detalles_serializados.append({
            'id_producto': detalle.id_producto.id_producto,
            'cantidad': int(detalle.cantidad_producto),
            'precioUnitario': float(detalle.precio_unitario or 0),
            'precioLista': float(detalle.precio_lista or detalle.id_producto.precio_actual or 0),
            'totalDetalle': float(detalle.total_detalle),
            'ivaDescripcion': int(detalle.id_producto.id_iva.descripcion),
            'total_iva_10': float(detalle.total_iva_10),
            'total_iva_5': float(detalle.total_iva_5),
            'nombre': detalle.id_producto.nombre,
        })

    context = {
        'venta': venta,
        'clientes': Cliente.objects.all().order_by('id_cliente'),
        'detalle_venta': detalle_venta,
        'productos': Producto.objects.all().order_by('nombre'),
        'detalle_tipo_pago': detalle_tipo_pago,
        'detalle_venta_json': json.dumps(detalles_serializados, cls=DjangoJSONEncoder),
        'tipo_venta': _tipos_de_venta_disponibles(),
        'monto_efectivo': monto_efectivo,
        'monto_pos': monto_pos,
        'monto_transferencia': monto_transferencia,
    }
    return render(request, 'ventas/editar_venta.html', context=context)


@login_required(login_url="/")
def ventasDeleteView(request, id_venta):
    venta = get_object_or_404(Venta, pk=id_venta)
    try:
        with transaction.atomic():
            detalles = VentaDetalle.objects.filter(id_venta=venta)
            _revertir_detalles_y_stock(
                detalles,
                request.user.id,
                referencia=f'VENTA-{venta.id_venta}-ELIMINADA',
                observacion='Reversion de stock por eliminacion de venta.',
            )
            detalles.delete()
            VentaTipoDePago.objects.filter(id_venta=venta).delete()
            venta.delete()
        messages.success(request, 'Venta eliminada correctamente.')
    except Exception as error:
        messages.error(request, f'No se pudo eliminar la venta: {error}')
        logging.error('Error al eliminar venta: %s', error)
    return redirect('ventas:ventas')


@login_required(login_url="/")
def ventaDetalleView(request, id_venta):
    venta = get_object_or_404(Venta, id_venta=id_venta)
    detalle_venta = VentaDetalle.objects.filter(id_venta=id_venta).select_related('id_producto')
    context = {
        'venta': venta,
        'detalle_venta': detalle_venta,
    }
    return render(request, 'ventas/detalle_venta.html', context=context)


@login_required(login_url="/")
def historialDeVentasView(request):
    ventas_agrupadas = Venta.objects.annotate(fecha=TruncDate('fecha_venta')) \
        .values('fecha') \
        .annotate(total_ventas=Sum('total_venta')) \
        .order_by('-fecha')

    paginator = Paginator(ventas_agrupadas, 10)
    ventas_por_pagina = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'ventas/ventas_historial.html', {'ventas_agrupadas': ventas_por_pagina})
