import pytz
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Producto, Categoria
from .forms import ProductoForm
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto
from Sucursales.models import Sucursal

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
    sucursal = get_sucursal_contexto(request)

    # ── Filtro base por sucursal ──────────────────────
    productos = Producto.objects.filter(activo=True).select_related('categoria', 'sucursal')
    if sucursal:
        productos = productos.filter(sucursal=sucursal)

    # ── Filtros de búsqueda ───────────────────────────
    sucursal_id  = request.GET.get('sucursal', '')
    categoria_id = request.GET.get('categoria', '')
    busqueda     = request.GET.get('q', '')

    if sucursal_id and request.user.es_duena:
        productos = productos.filter(sucursal__id=sucursal_id)
    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    # ── Paginación ────────────────────────────────────
    paginator   = Paginator(productos, 10)
    page_obj    = paginator.get_page(request.GET.get('page', 1))

    # ── Métricas (filtradas por sucursal) ─────────────
    qs_base       = Producto.objects.filter(activo=True)
    if sucursal:
        qs_base = qs_base.filter(sucursal=sucursal)

    total_productos = qs_base.count()
    criticos        = sum(1 for p in qs_base if p.estado() in ('critico', 'agotado'))
    optimos         = sum(1 for p in qs_base if p.estado() == 'optimo')
    eficiencia      = int((optimos / total_productos * 100)) if total_productos > 0 else 0

    from Sucursales.models import Sucursal as SucursalModel
    sucursales_activas = SucursalModel.objects.filter(activa=True)
    sucursales_count   = sucursales_activas.count()

    # ── Formulario nuevo producto ─────────────────────
    form = ProductoForm()
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo = form.save(commit=False)
            if sucursal and not nuevo.sucursal:
                nuevo.sucursal = sucursal
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
        'sucursales':       sucursales_activas,
        'categorias':       Categoria.objects.all(),
        'sucursal_sel':     sucursal_id,
        'categoria_sel':    categoria_id,
        'busqueda':         busqueda,
        'form':             form,
        'sucursal_actual':  sucursal,
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Inventario/Inventario.html', context)

from django.http import HttpResponse

@login_required(login_url='/')
@cualquier_rol
def exportar_inventario(request):
    return HttpResponse("Exportación de inventario")

