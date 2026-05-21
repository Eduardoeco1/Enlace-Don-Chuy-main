from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import EntradaInsumo
from .forms import EntradaInsumoForm

# ── IMPORTAMOS EL SELECTOR GLOBAL ──
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


@login_required(login_url='/')
@cualquier_rol
def entrada_mercancia_view(request):
    """
    Vista para registrar entradas de mercancía de forma dinámica.
    Al guardar, el signal se encarga de sincronizar con Inventario.
    """
    # ── INTEGRACIÓN DEL SELECTOR GLOBAL OFICIAL ──
    sucursal = get_sucursal_contexto(request)

    # Evaluar el rol del usuario de forma segura
    es_duena = (
        request.user.is_superuser or 
        (hasattr(request.user, 'rol') and request.user.rol == 'duena') or 
        request.user.groups.filter(name='Dueña').exists()
    )

    if request.method == 'POST':
        # Pasamos de forma explícita request.POST, user y sucursal_actual desde el contexto
        form = EntradaInsumoForm(
            request.POST, 
            user=request.user, 
            sucursal_actual=sucursal
        )
        
        if form.is_valid():
            entrada = form.save(commit=False)
            
            # Regla de Negocio: Si NO es dueña, se le fuerza rigurosamente su sucursal del contexto fijo
            if not es_duena and sucursal:
                entrada.sucursal = sucursal
                
            entrada.save()
            
            # Mensaje de éxito detallado
            messages.success(
                request, 
                f'✅ Entrada registrada: {entrada.producto} ({entrada.cantidad}). '
                f'El inventario se actualizará automáticamente.'
            )
            return redirect('EntradaMercancia:entrada')
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')
            
    else:
        # En peticiones GET inicializamos el formulario pasándole el usuario y el contexto actual
        form = EntradaInsumoForm(
            user=request.user, 
            sucursal_actual=sucursal
        )

    # ── Obtener historial de entradas ───────────────────
    # Optimizamos consultas SQL con select_related('sucursal')
    entradas = EntradaInsumo.objects.select_related('sucursal').all()
    
    # ── FILTRO DINÁMICO ──
    if sucursal:
        entradas = entradas.filter(sucursal=sucursal)
    
    # Ordenar por fecha de creación descendente y limitar a los últimos 20 registros
    entradas = entradas.order_by('-creado_en')[:20]

    context = {
        'form':             form,
        'entradas':         entradas,
        # 'sucursal_actual' ya no hace falta pasarlo aquí, el context_processor lo manda al HTML.
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'EntradaMercancia/enmer.html', context)









