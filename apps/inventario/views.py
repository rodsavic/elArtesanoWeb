from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render

from apps.inventario.models import MovimientoProducto
from apps.inventario.services import registrar_movimiento_producto
from apps.productos.models import Producto


@login_required(login_url='/')
def inventarioReadView(request):
    query = (request.GET.get('q') or '').strip()
    movimientos = MovimientoProducto.objects.select_related('producto').all()
    if query:
        movimientos = movimientos.filter(producto__nombre__icontains=query)

    paginator = Paginator(movimientos, 12)
    items_page = paginator.get_page(request.GET.get('page'))
    context = {
        'items_page': items_page,
        'query': query,
    }
    return render(request, 'inventario/inventario.html', context=context)


@login_required(login_url='/')
def inventarioCreateView(request):
    productos = Producto.objects.all().order_by('nombre')

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        tipo_movimiento = request.POST.get('tipo_movimiento')
        cantidad = request.POST.get('cantidad')
        observacion = (request.POST.get('observacion') or '').strip()
        fecha_movimiento = request.POST.get('fecha_movimiento')

        if not producto_id:
            messages.error(request, 'Debes seleccionar un producto.')
            return render(request, 'inventario/inventario_create.html', {'productos': productos})

        try:
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(id_producto=producto_id)
                registrar_movimiento_producto(
                    producto=producto,
                    tipo_movimiento=tipo_movimiento,
                    cantidad=cantidad,
                    usuario_id=request.user.id,
                    referencia='MOVIMIENTO-MANUAL',
                    observacion=observacion,
                    fecha_movimiento=fecha_movimiento,
                )
            messages.success(request, 'Movimiento registrado exitosamente.')
            return redirect('inventario:inventario')
        except Producto.DoesNotExist:
            messages.error(request, 'El producto seleccionado no existe.')
        except ValueError as error:
            messages.error(request, str(error))

    return render(request, 'inventario/inventario_create.html', {'productos': productos})
