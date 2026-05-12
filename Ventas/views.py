import json
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Categoria, Producto, Pedido, DetallePedido
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto

IVA_TASA = Decimal('0.16')


@login_required(login_url='/')
@cualquier_rol
def pos_view(request):
    sucursal     = get_sucursal_contexto(request)
    categoria_id = request.GET.get('categoria', '')
    busqueda     = request.GET.get('q', '')

    categorias = Categoria.objects.all()

    # ── Filtro productos por sucursal ─────────────────
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')
    if sucursal:
        productos = productos.filter(sucursal=sucursal)

    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    ultimo = Pedido.objects.order_by('-id').first()
    ticket = f'#{(ultimo.id + 1):04d}' if ultimo else '#0001'

    context = {
        'categorias':     categorias,
        'productos':      productos,
        'categoria_sel':  categoria_id,
        'busqueda':       busqueda,
        'ticket':         ticket,
        'sucursal_actual': sucursal,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
        'usuario_rol':    request.user.get_rol_display() if hasattr(request.user, 'get_rol_display') else '',
    }
    return render(request, 'Ventas/Ventas.html', context)


@login_required(login_url='/')
@require_POST
@cualquier_rol
def procesar_venta(request):
    try:
        data     = json.loads(request.body)
        tipo     = data.get('tipo', 'llevar')
        items    = data.get('items', [])
        sucursal = get_sucursal_contexto(request)

        if not items:
            return JsonResponse({'ok': False, 'error': 'El pedido está vacío.'}, status=400)

        ultimo = Pedido.objects.order_by('-id').first()
        num    = (ultimo.id + 1) if ultimo else 1
        ticket = f'#{num:04d}'

        pedido = Pedido.objects.create(
            ticket   = ticket,
            tipo     = tipo,
            estado   = 'procesado',
            cajero   = request.user,
            sucursal = sucursal,
        )

        subtotal = Decimal('0')

        for item in items:
            # Valida que el producto pertenezca a la sucursal del usuario
            qs = Producto.objects.filter(id=item['producto_id'], activo=True)
            if sucursal:
                qs = qs.filter(sucursal=sucursal)

            producto = qs.get()
            cantidad = int(item.get('cantidad', 1))

            DetallePedido.objects.create(
                pedido   = pedido,
                producto = producto,
                cantidad = cantidad,
                precio_u = producto.precio,
                notas    = item.get('notas', ''),
            )

            if producto.stock >= cantidad:
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])

            subtotal += producto.precio * cantidad

        iva   = (subtotal * IVA_TASA).quantize(Decimal('0.01'))
        total = subtotal + iva

        pedido.subtotal = subtotal
        pedido.iva      = iva
        pedido.total    = total
        pedido.save()

        return JsonResponse({
            'ok':       True,
            'ticket':   pedido.ticket,
            'sucursal': sucursal.nombre if sucursal else 'Global',
            'subtotal': float(subtotal),
            'iva':      float(iva),
            'total':    float(total),
        })

    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no disponible en tu sucursal.'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
    


