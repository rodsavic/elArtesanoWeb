from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.gastos.models import Gasto


def _build_querystring(request):
    querydict = request.GET.copy()
    querydict.pop('page', None)
    encoded = querydict.urlencode()
    return f'&{encoded}' if encoded else ''


@login_required(login_url="/")
def gastosReadView(request):
    fecha_desde = (request.GET.get('fecha_desde') or '').strip()
    fecha_hasta = (request.GET.get('fecha_hasta') or '').strip()
    nombre = (request.GET.get('nombre') or '').strip()
    orden_monto = (request.GET.get('orden_monto') or '').strip()

    gastos = Gasto.objects.all()

    if fecha_desde:
        gastos = gastos.filter(fecha_gasto__gte=fecha_desde)
    if fecha_hasta:
        gastos = gastos.filter(fecha_gasto__lte=fecha_hasta)
    if nombre:
        gastos = gastos.filter(Q(nombre__icontains=nombre))

    if orden_monto == 'asc':
        gastos = gastos.order_by('monto', '-fecha_gasto')
    elif orden_monto == 'desc':
        gastos = gastos.order_by('-monto', '-fecha_gasto')

    total_filtrado = gastos.aggregate(total=Sum('monto'))['total'] or 0
    hoy = timezone.localdate()
    total_mes_actual = Gasto.objects.filter(
        fecha_gasto__year=hoy.year,
        fecha_gasto__month=hoy.month,
    ).aggregate(total=Sum('monto'))['total'] or 0

    paginator = Paginator(gastos, 12)
    items_page = paginator.get_page(request.GET.get('page'))

    context = {
        'items_page': items_page,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'nombre': nombre,
        'orden_monto': orden_monto,
        'total_filtrado': total_filtrado,
        'total_mes_actual': total_mes_actual,
        'current_query': _build_querystring(request),
    }
    return render(request, 'gastos/gastos.html', context=context)


@login_required(login_url="/")
def gastoCreateView(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        monto = request.POST.get('monto')
        fecha_gasto = request.POST.get('fecha_gasto') or timezone.localdate()

        if not nombre:
            messages.error(request, 'Debes ingresar el nombre de la compra.')
            return redirect('gastos:crear_gasto')

        try:
            Gasto.objects.create(
                nombre=nombre,
                monto=monto,
                fecha_gasto=fecha_gasto,
                usuario_creacion=request.user.id,
            )
            messages.success(request, 'Gasto registrado exitosamente.')
            return redirect('gastos:gastos')
        except Exception as error:
            messages.error(request, f'No se pudo registrar el gasto: {error}')
            return redirect('gastos:crear_gasto')

    return render(request, 'gastos/crear_gasto.html', {
        'fecha_actual': timezone.localdate().isoformat(),
    })


@login_required(login_url="/")
def gastoUpdateView(request, id_gasto):
    gasto = get_object_or_404(Gasto, id_gasto=id_gasto)

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        monto = request.POST.get('monto')
        fecha_gasto = request.POST.get('fecha_gasto') or timezone.localdate()

        if not nombre:
            messages.error(request, 'Debes ingresar el nombre de la compra.')
            return redirect('gastos:editar_gasto', id_gasto=id_gasto)

        try:
            gasto.nombre = nombre
            gasto.monto = monto
            gasto.fecha_gasto = fecha_gasto
            gasto.save()
            messages.success(request, 'Gasto actualizado exitosamente.')
            return redirect('gastos:gastos')
        except Exception as error:
            messages.error(request, f'No se pudo actualizar el gasto: {error}')
            return redirect('gastos:editar_gasto', id_gasto=id_gasto)

    return render(request, 'gastos/editar_gasto.html', {
        'gasto': gasto,
    })


@login_required(login_url="/")
def gastoDeleteView(request, id_gasto):
    gasto = get_object_or_404(Gasto, id_gasto=id_gasto)
    gasto.delete()
    messages.success(request, 'Gasto eliminado correctamente.')
    return redirect('gastos:gastos')
