import json
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction

from Inventario.models import Producto as ProductoInventario
from Inventario.models import Categoria as CategoriaInventario
from .models import Pedido, DetallePedido

from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


def _es_duena(user):
    return (
        user.is_superuser or
        (hasattr(user, 'rol') and user.rol in ['duena', 'dueña']) or
        user.groups.filter(name='Dueña').exists()
    )


def _obtener_sucursal_usuario(request):
    sucursal = get_sucursal_contexto(request)
    es_duena = _es_duena(request.user)

    if not es_duena:
        if hasattr(request.user, 'empleado') and request.user.empleado.sucursal:
            sucursal = request.user.empleado.sucursal
        elif hasattr(request.user, 'sucursal') and request.user.sucursal:
            sucursal = request.user.sucursal

    return sucursal, es_duena


@login_required(login_url='/')
@cualquier_rol
def pos_view(request):
    sucursal, es_duena = _obtener_sucursal_usuario(request)

    categoria_id = request.GET.get('categoria', '')
    busqueda = request.GET.get('q', '')

    categorias = CategoriaInventario.objects.all()

    productos = ProductoInventario.objects.filter(
        activo=True,
        stock__gt=0,
    ).select_related('categoria', 'sucursal')

    if sucursal:
        productos = productos.filter(sucursal=sucursal)
    elif not es_duena:
        productos = productos.none()

    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    productos = productos.distinct()

    ultimo = Pedido.objects.order_by('-id').first()
    ticket = f'#{(ultimo.id + 1):04d}' if ultimo else '#0001'

    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_sel': categoria_id,
        'busqueda': busqueda,
        'ticket': ticket,
        'sucursal_actual': sucursal,
        'es_duena': es_duena,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'Ventas/Ventas.html', context)


@login_required(login_url='/')
@require_POST
@cualquier_rol
def procesar_venta(request):
    try:
        data = json.loads(request.body)

        tipo_servicio = data.get('tipo', 'llevar')
        metodo_pago = data.get('metodo', 'efectivo')
        items = data.get('items', [])

        sucursal, es_duena = _obtener_sucursal_usuario(request)

        if not sucursal:
            return JsonResponse({
                'ok': False,
                'error': '⚠️ Debes tener una sucursal activa para procesar la venta.'
            }, status=400)

        if not items:
            return JsonResponse({
                'ok': False,
                'error': 'El pedido está vacío.'
            }, status=400)

        with transaction.atomic():
            ultimo = Pedido.objects.select_for_update().order_by('-id').first()
            num = (ultimo.id + 1) if ultimo else 1
            ticket = f'#{num:04d}'

            pedido = Pedido.objects.create(
                ticket=ticket,
                tipo=tipo_servicio,
                metodo_pago=metodo_pago,
                estado='procesado',
                cajero=request.user,
                sucursal=sucursal,
            )

            subtotal = Decimal('0.00')

            for item in items:
                producto = ProductoInventario.objects.filter(
                    id=item.get('producto_id'),
                    activo=True,
                    sucursal=sucursal,
                ).first()

                if not producto:
                    return JsonResponse({
                        'ok': False,
                        'error': 'El producto no pertenece a la sucursal activa.'
                    }, status=404)

                cantidad = int(item.get('cantidad', 1))

                if cantidad <= 0:
                    return JsonResponse({
                        'ok': False,
                        'error': 'La cantidad debe ser mayor a 0.'
                    }, status=400)

                if producto.stock < cantidad:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Stock insuficiente para {producto.nombre}.'
                    }, status=400)

                precio_unitario = producto.precio if producto.precio else Decimal('0.00')

                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_u=precio_unitario,
                    notas=item.get('notas', ''),
                )

                producto.stock -= cantidad
                producto.save(update_fields=['stock'])

                subtotal += precio_unitario * cantidad

            pedido.subtotal = subtotal
            pedido.total = subtotal
            pedido.save(update_fields=['subtotal', 'total'])

        return JsonResponse({
            'ok': True,
            'ticket': ticket,
            'total': float(subtotal)
        })

    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)