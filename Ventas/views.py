import json
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages

# Modelos e Imports
from Inventario.models import Producto as ProductoInventario
from Inventario.models import Categoria as CategoriaInventario
from .models import Pedido, DetallePedido

# ── IMPORTAMOS EL SELECTOR GLOBAL OFICIAL ──
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


@login_required(login_url='/')
@cualquier_rol
def pos_view(request):
    """
    Vista del Punto de Venta (POS).
    Filtra estrictamente por la sucursal seleccionada.
    """
    # 1. Obtenemos la sucursal de la sesión global (si es None, estamos en "Todas")
    sucursal = get_sucursal_contexto(request)
    
    categoria_id = request.GET.get('categoria', '')
    busqueda = request.GET.get('q', '')

    categorias = CategoriaInventario.objects.all()

    # 2. Base de productos: Activos y con stock
    productos = ProductoInventario.objects.filter(
        activo=True,
        stock__gt=0,
    ).select_related('categoria', 'sucursal')

    # 3. FILTRADO ESTRICTO POR SUCURSAL
    # Si la dueña eligió una sucursal específica (o es un empleado), filtramos.
    # Si la dueña eligió "Todas", productos contiene todo el catálogo global.
    if sucursal:
        productos = productos.filter(sucursal_id=sucursal.id)

    # 4. Filtros adicionales de UI
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    # 5. Evitar duplicados visuales por uniones de SQL
    productos = productos.distinct()

    ultimo = Pedido.objects.order_by('-id').first()
    ticket = f'#{(ultimo.id + 1):04d}' if ultimo else '#0001'

    context = {
        'categorias': categorias,
        'productos': productos,
        'categoria_sel': categoria_id,
        'busqueda': busqueda,
        'ticket': ticket,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Ventas/Ventas.html', context)


@login_required(login_url='/')
@require_POST
@cualquier_rol
def procesar_venta(request):
    """
    Procesar venta de manera atómica reduciendo inventario.
    Aquí se valida estrictamente que el producto pertenezca a la sucursal.
    """
    try:
        data = json.loads(request.body)
        tipo_servicio = data.get('tipo', 'llevar')
        metodo_pago = data.get('metodo', 'efectivo')
        items = data.get('items', [])
        
        sucursal = get_sucursal_contexto(request)

        # ── CANDADO DE SEGURIDAD ──
        if not sucursal:
            return JsonResponse({
                'ok': False, 
                'error': '⚠️ Para cobrar, debes seleccionar una sucursal específica en el menú superior.'
            }, status=400)

        if not items:
            return JsonResponse({'ok': False, 'error': 'El pedido está vacío.'}, status=400)

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
            subtotal = Decimal('0')

            for item in items:
                # 🔒 Validación estricta: El producto DEBE pertenecer a esta sucursal
                qs = ProductoInventario.objects.filter(
                    id=item['producto_id'], 
                    activo=True,
                    sucursal_id=sucursal.id
                )

                if not qs.exists():
                    return JsonResponse({'ok': False, 'error': f'El producto no pertenece a la sucursal activa.'}, status=404)
                
                producto = qs.get()
                cantidad = int(item.get('cantidad', 1))

                if producto.stock < cantidad:
                    return JsonResponse({
                        'ok': False,
                        'error': f'Stock insuficiente para {producto.nombre}.'
                    }, status=400)

                precio_unitario = producto.precio if hasattr(producto, 'precio') else Decimal('0')

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

        return JsonResponse({'ok': True, 'ticket': ticket, 'total': float(subtotal)})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error interno: {str(e)}'}, status=500)







