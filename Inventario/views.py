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

# ── IMPORTAMOS LOS DECORADORES (Eliminamos get_sucursal_contexto) ──
from Sucursales.permisos import cualquier_rol, gerente_o_superior

def _get_saludo_cdmx():
    """Retorna un saludo basado en la hora de CDMX."""
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
    # 1. QuerySet base inicial (Solo productos activos)
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')

    # 2. Captura de parámetros desde los filtros complementarios
    categoria_id = request.GET.get('categoria', '')
    busqueda     = request.GET.get('q', '')

    # 3. ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal_actual = getattr(request, 'sucursal_actual', None)
    
    # Validamos rol dueña para habilitar asignación a diferentes sucursales
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

    # 4. Aplicación de filtros complementarios de búsqueda
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    # 5. Paginación de los resultados finales
    paginator = Paginator(productos, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    # 6. Métricas optimizadas basadas en el contexto purificado
    total_productos = productos.count()
    criticos        = sum(1 for p in productos if p.estado() in ('critico', 'agotado'))
    optimos         = sum(1 for p in productos if p.estado() == 'optimo')
    eficiencia      = int((optimos / total_productos * 100)) if total_productos > 0 else 0

    sucursales_activas = Sucursal.objects.filter(activa=True)
    sucursales_count   = sucursales_activas.count()

    # 7. Formulario para agregar un nuevo producto
    form = ProductoForm()
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo = form.save(commit=False)
            
            # Asignación automática de sucursal resguardando pertenencias
            if not es_duena and sucursal_actual:
                # Gerente/Empleado forza su sucursal
                nuevo.sucursal = sucursal_actual
            elif es_duena:
                # Dueña elige a qué sucursal va desde el formulario o hereda la del filtro
                if request.POST.get('sucursal'):
                    try:
                        nuevo.sucursal = Sucursal.objects.get(id=request.POST.get('sucursal'))
                    except Sucursal.DoesNotExist:
                        pass
                elif sucursal_actual:
                    nuevo.sucursal = sucursal_actual
            
            nuevo.save()
            messages.success(request, f'✅ Producto "{nuevo.nombre}" agregado correctamente.')
            return redirect('Inventario:inventario')
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')

    context = {
        'saludo':           _get_saludo_cdmx(),
        'page_obj':         page_obj,
        'total_productos':  total_productos,
        'criticos':         criticos,
        'sucursales_count': sucursales_count,
        'eficiencia':       eficiencia,
        'categorias':       Categoria.objects.all(),
        'sucursal_sel':     sucursal_id,
        'categoria_sel':    categoria_id,
        'busqueda':         busqueda,
        'form':             form,
        # 'sucursales', 'sucursal_actual' y 'es_duena' vienen automáticos del context_processor
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Inventario/Inventario.html', context)


@login_required(login_url='/')
@cualquier_rol
def exportar_inventario(request):
    """Exporta el inventario a CSV respetando el contexto global seleccionado"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="inventario.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow([
        'Producto', 'Categoría', 'Sucursal', 'Stock', 
        'Unidad', 'Stock Mínimo', 'Estado', 'Activo'
    ])
    
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
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
            'Sí' if producto.activo else 'No'
        ])
    
    return response


@login_required(login_url='/')
@gerente_o_superior
def editar_producto(request, producto_id):
    """Vista para editar producto del inventario con control estricto de acceso"""
    producto = get_object_or_404(Producto, id=producto_id)
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal_actual = getattr(request, 'sucursal_actual', None)
    
    es_duena = (
        request.user.is_superuser or 
        (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or 
        request.user.groups.filter(name='Dueña').exists()
    )
    
    # Control de seguridad: Si no es dueña, el gerente no puede editar productos fuera de su contexto
    if not es_duena and sucursal_actual and producto.sucursal != sucursal_actual:
        messages.error(request, '🚫 No tienes permiso para editar este producto.')
        return redirect('Inventario:inventario')
    
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre', producto.nombre)
        producto.precio = request.POST.get('precio', producto.precio)
        producto.stock_minimo = request.POST.get('stock_minimo', producto.stock_minimo)
        producto.activo = request.POST.get('activo') == 'on'
        
        categoria_id = request.POST.get('categoria')
        if categoria_id:
            try:
                producto.categoria = Categoria.objects.get(id=categoria_id)
            except Categoria.DoesNotExist:
                pass
        
        producto.save()
        messages.success(request, f'✅ Producto "{producto.nombre}" actualizado correctamente.')
        return redirect('Inventario:inventario')
    
    context = {
        'producto':        producto,
        'categorias':      Categoria.objects.all(),
        # No pasamos 'sucursal_actual' para evitar sobreescribir el del context_processor
        'usuario_nombre':  request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Inventario/editar_producto.html', context)


@login_required(login_url='/')
@gerente_o_superior
@require_POST
def actualizar_precio_rapido(request, producto_id):
    """Actualizar precio de producto vía AJAX resguardando el contexto de sucursal"""
    try:
        data = json.loads(request.body)
        precio = data.get('precio')
        
        producto = get_object_or_404(Producto, id=producto_id)
        # ── MODIFICACIÓN: Leer directamente del Middleware ──
        sucursal_actual = getattr(request, 'sucursal_actual', None)
        
        es_duena = (
            request.user.is_superuser or 
            (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or 
            request.user.groups.filter(name='Dueña').exists()
        )
        
        # Validación de seguridad para peticiones asíncronas
        if not es_duena and sucursal_actual and producto.sucursal != sucursal_actual:
            return JsonResponse({'ok': False, 'error': 'Sin permisos sobre esta sucursal'}, status=403)
        
        producto.precio = precio
        producto.save(update_fields=['precio'])
        
        return JsonResponse({
            'ok': True,
            'mensaje': f'Precio actualizado: ${precio}'
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    
    




    