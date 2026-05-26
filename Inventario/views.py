import pytz
import csv
import json
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Producto, Categoria
from .forms import ProductoForm
from Sucursales.models import Sucursal
from Sucursales.permisos import cualquier_rol, gerente_o_superior


def _get_saludo_cdmx():
    tz_cdmx = pytz.timezone('America/Mexico_City')
    hora = datetime.now(tz_cdmx).hour

    if 6 <= hora < 12:
        return 'Buenos días'
    elif 12 <= hora < 19:
        return 'Buenas tardes'
    else:
        return 'Buenas noches'


@login_required(login_url='/')
@cualquier_rol
def inventario_view(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')

    categoria_id = request.GET.get('categoria', '')
    busqueda = request.GET.get('q', '')

    sucursal_actual = getattr(request, 'sucursal_actual', None)

    es_duena = (
        request.user.is_superuser or
        (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or
        request.user.groups.filter(name='Dueña').exists()
    )

    if sucursal_actual:
        productos = productos.filter(sucursal=sucursal_actual)
        sucursal_id = str(sucursal_actual.id)
    else:
        sucursal_id = ''

    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    paginator = Paginator(productos, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    total_productos = productos.count()
    criticos = sum(1 for p in productos if p.estado() in ('critico', 'agotado'))
    optimos = sum(1 for p in productos if p.estado() == 'optimo')
    eficiencia = int((optimos / total_productos * 100)) if total_productos > 0 else 0

    sucursales_activas = Sucursal.objects.filter(activa=True)
    sucursales_count = sucursales_activas.count()

    form = ProductoForm()

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)

        if form.is_valid():
            nuevo = form.save(commit=False)

            if not es_duena and sucursal_actual:
                nuevo.sucursal = sucursal_actual

            elif es_duena:
                sucursal_post = request.POST.get('sucursal')

                if sucursal_post:
                    nuevo.sucursal = Sucursal.objects.filter(id=sucursal_post).first()

                elif sucursal_actual:
                    nuevo.sucursal = sucursal_actual

            if not nuevo.sucursal:
                messages.error(request, '❌ Debes seleccionar una sucursal.')
                return redirect('Inventario:inventario')

            nuevo.save()
            messages.success(request, f'✅ Producto "{nuevo.nombre}" agregado correctamente.')
            return redirect('Inventario:inventario')

        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')

    context = {
        'saludo': _get_saludo_cdmx(),
        'page_obj': page_obj,
        'total_productos': total_productos,
        'criticos': criticos,
        'sucursales_count': sucursales_count,
        'eficiencia': eficiencia,
        'categorias': Categoria.objects.all(),
        'sucursales': Sucursal.objects.filter(activa=True),
        'sucursal_sel': sucursal_id,
        'categoria_sel': categoria_id,
        'busqueda': busqueda,
        'form': form,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'Inventario/Inventario.html', context)


@login_required(login_url='/')
@cualquier_rol
def exportar_inventario(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Producto',
        'Categoría',
        'Sucursal',
        'Stock',
        'Unidad',
        'Stock Mínimo',
        'Estado',
        'Activo',
    ])

    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')

    sucursal_actual = getattr(request, 'sucursal_actual', None)

    if sucursal_actual:
        productos = productos.filter(sucursal=sucursal_actual)

    for producto in productos:
        writer.writerow([
            producto.nombre,
            producto.categoria.nombre if producto.categoria else '',
            producto.sucursal.nombre if producto.sucursal else '',
            float(producto.stock),
            producto.unidad,
            float(producto.stock_minimo),
            producto.estado_display() if hasattr(producto, 'estado_display') else producto.estado(),
            'Sí' if producto.activo else 'No',
        ])

    return response


@login_required(login_url='/')
@gerente_o_superior
def editar_producto(request, producto_id):
    import re
    from decimal import Decimal

    producto = get_object_or_404(Producto, id=producto_id)
    sucursal_actual = getattr(request, 'sucursal_actual', None)

    es_duena = (
        request.user.is_superuser or
        (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or
        request.user.groups.filter(name='Dueña').exists()
    )

    if not es_duena and sucursal_actual and producto.sucursal != sucursal_actual:
        messages.error(request, '🚫 No tienes permiso para editar este producto.')
        return redirect('Inventario:inventario')

    if request.method == 'POST':

        nombre_post = request.POST.get('nombre', '').strip()

        # VALIDAR SOLO LETRAS
        if not re.fullmatch(r'[A-Za-zÁÉÍÓÚáéíóúÑñ ]+', nombre_post):
            messages.error(
                request,
                '❌ El nombre solo puede contener letras y espacios.'
            )
            return redirect(
                'Inventario:editar_producto',
                producto_id=producto.id
            )

        # VALIDAR STOCK MINIMO ENTERO
        stock_minimo_post = request.POST.get('stock_minimo', '0')

        try:
            stock_minimo_decimal = Decimal(stock_minimo_post)

            if stock_minimo_decimal != int(stock_minimo_decimal):
                raise ValueError

        except Exception:
            messages.error(
                request,
                '❌ El stock mínimo debe ser un número entero.'
            )
            return redirect(
                'Inventario:editar_producto',
                producto_id=producto.id
            )

        producto.nombre = nombre_post
        producto.precio = request.POST.get('precio', producto.precio)
        producto.stock_minimo = int(stock_minimo_decimal)
        producto.activo = request.POST.get('activo') == 'on'

        categoria_id = request.POST.get('categoria')

        if categoria_id:
            producto.categoria = Categoria.objects.filter(
                id=categoria_id
            ).first()
        else:
            producto.categoria = None

        sucursal_id = request.POST.get('sucursal')

        if sucursal_id:
            producto.sucursal = Sucursal.objects.filter(
                id=sucursal_id
            ).first()

        elif not producto.sucursal:
            messages.error(
                request,
                '❌ Debes seleccionar una sucursal.'
            )
            return redirect(
                'Inventario:editar_producto',
                producto_id=producto.id
            )

        if request.FILES.get('imagen'):
            producto.imagen = request.FILES.get('imagen')

        producto.save()

        messages.success(
            request,
            f'✅ Producto "{producto.nombre}" actualizado correctamente.'
        )

        return redirect('Inventario:inventario')

    context = {
        'producto': producto,
        'categorias': Categoria.objects.all(),
        'sucursales': Sucursal.objects.filter(activa=True),
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(
        request,
        'Inventario/editar_producto.html',
        context
    )

@login_required(login_url='/')
@gerente_o_superior
@require_POST
def actualizar_precio_rapido(request, producto_id):
    try:
        data = json.loads(request.body)
        precio = data.get('precio')

        producto = get_object_or_404(Producto, id=producto_id)
        sucursal_actual = getattr(request, 'sucursal_actual', None)

        es_duena = (
            request.user.is_superuser or
            (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or
            request.user.groups.filter(name='Dueña').exists()
        )

        if not es_duena and sucursal_actual and producto.sucursal != sucursal_actual:
            return JsonResponse({'ok': False, 'error': 'Sin permisos sobre esta sucursal'}, status=403)

        producto.precio = precio
        producto.save(update_fields=['precio'])

        return JsonResponse({
            'ok': True,
            'mensaje': f'Precio actualizado: ${precio}',
        })

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required(login_url='/')
def eliminar_producto(request, producto_id):
    if request.user.rol not in ['duena', 'gerente', 'dueña'] and not request.user.is_superuser:
        messages.error(request, '❌ No tienes permisos para eliminar productos.')
        return redirect('Inventario:inventario')

    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()

    messages.success(request, '✅ Producto eliminado correctamente.')
    return redirect('Inventario:inventario')


