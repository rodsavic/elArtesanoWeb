import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages
from .forms import *
from django.core.paginator import Paginator

@login_required(login_url="/")
def productosReadView(request):
    query = request.GET.get('q')
    productos = Producto.objects.all().order_by('nombre')

    if query:
        productos = productos.filter(nombre__icontains=query)

    columnas = ['Nombre','Precio Actual','Stock Minimo','Stock Actual','Costo Actual']
    paginator = Paginator(productos,10)
    page_number = request.GET.get('page')
    items_page=paginator.get_page(page_number)
    context = {
        'columnas':columnas,
        'productos':productos,
        'items_page': items_page,
        'query': query
    }

    return render(request, 'productos/productos.html', context=context)

@login_required(login_url="/")
def createProductosView(request):
    if request.method == 'POST':
        form = ProductosForm(request.POST)
        if form.is_valid():
            try:
                productoNuevo = form.save(commit=False)
                productoNuevo.usuario_creacion = request.user.id
                productoNuevo.save()
                messages.success(request, 'Producto creado exitosamente')
                return redirect('productos:productos')
            except Exception as e:
                error_message = str(e)  # Captura el mensaje de error
                messages.error(request, f'Error en el servidor: {error_message}')
                logging.error(f'Error al crear producto: {error_message}')  # O puedes registrar el error en un archivo de log
                return redirect('productos:productos')
        else:
            # Datos invalidos en el formulario, renderizamos de nuevo con los errores
            if 'nombre' in form.errors:
                messages.error(request, 'El nombre ya existe!',
                              extra_tags="Verificalo e intenta de nuevo.")
            return render(request, 'productos/crear_productos.html', {'form': form})
    else:
        form = ProductosForm()

    return render(request,'productos/crear_productos.html',{'form':form})


@login_required(login_url="/")
def ProductoUpdateView(request, id_producto):
    """Vista para modificar producto"""
    producto = Producto.objects.get(id_producto=id_producto)
    # Si se desea guardar en la BDD
    if request.method == 'POST':
        # Creamos una instancia de formulario y la llenamos con el data del request:
        form = ProductosForm(request.POST, instance=producto)
        # Si no se han hecho modificaciones
        if not form.has_changed():
            messages.info(request, "No ha hecho ningun cambio", extra_tags=" ")
            return redirect('productos:productos')
        # Verificamos que los datos sean validos:
        if form.is_valid():
            form.save()
            messages.success(request, 'producto: ' +
                             request.POST['nombre'] + ' modificado exitosamente!', extra_tags=" ")
            return redirect('productos:productos')
        else:
            # Datos invalidos en el formulario, renderizamos de nuevo con los errores
            if 'nombre' in form.errors:
                messages.info(request, 'El nombre ya existe!',
                              extra_tags="Verifica e intenta de nuevo.")
            return render(request, 'productos/editar_producto.html',
                          {'form': form, 'producto': producto})
    else:
        # Si es una solicitud GET envia el template
        context = {
            'resaltar_boton': 'stock-productos',
            'form': ProductosForm(instance=producto),
            'producto': producto
        }
        return render(request, 'productos/editar_producto.html', context=context)

@login_required(login_url="/")
def productoDeleteView(request, id_producto):
    producto = get_object_or_404(Producto, pk=id_producto)
    producto.delete()
    messages.success(request,"Producto eliminado correctamente")
    return redirect('productos:productos')


def productos_json(request):
    productos = list(
        Producto.objects.order_by('nombre').values(
            "id_producto",
            "nombre",
            "precio_actual",
            "stock_minimo",
            "stock_actual",
            "costo_actual",
        )
    )
    return JsonResponse(productos, safe=False)
