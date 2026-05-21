from decimal import Decimal
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum

from .models import CierreCaja
from .forms import CierreCajaForm
from Sucursales.permisos import gerente_o_superior, get_sucursal_contexto


def _calcular_ventas_dia(sucursal=None):
    """
    Calcula las ventas reales del día desde el modelo Pedido.
    Agrupa y suma dinámicamente según el método de pago real ('tipo').
    """
    from Ventas.models import Pedido

    # Usar hora local de la sucursal para evitar desfase de fecha con UTC
    hoy = timezone.now().date()

    # Obtener pedidos del día con estado procesado
    pedidos = Pedido.objects.filter(
        creado_en__date=hoy,
        estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
    )
    
    # ── FILTRO DINÁMICO ──
    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    # Calcular totales generales básicos
    total_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    num_pedidos = pedidos.count()

    # Inicializar los acumuladores de métodos de pago en 0
    ventas_efectivo = Decimal('0.00')
    ventas_tarjeta = Decimal('0.00')
    ventas_delivery = Decimal('0.00')

    # CALCULAR MÉTODOS DE PAGO CORRECTAMENTE (Usa tipo de Pedido)
    metodos_pago = pedidos.values('tipo').annotate(total=Sum('total'))

    # Asignar valores reales iterando sobre la agrupación de la BD
    for metodo in metodos_pago:
        nombre_metodo = str(metodo['tipo']).lower().strip() if metodo['tipo'] else ''
        monto = metodo['total'] or Decimal('0.00')

        if nombre_metodo == 'efectivo':
            ventas_efectivo = monto
        elif nombre_metodo == 'tarjeta':
            ventas_tarjeta = monto
        elif nombre_metodo in ['app', 'delivery', 'transferencia', 'plataforma']:
            ventas_delivery += monto

    return {
        'ventas_efectivo': ventas_efectivo,
        'ventas_tarjeta':   ventas_tarjeta,
        'ventas_delivery': ventas_delivery,
        'total_ventas':    total_dia,
        'num_pedidos':     num_pedidos,
    }


def _calcular_actividades_turno(sucursal=None):
    """
    Obtiene actividades del turno actual:
    entradas de mercancía, retiros y validaciones.
    """
    from EntradaMercancia.models import EntradaInsumo
    from Ventas.models import Pedido

    ahora      = timezone.now()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    actividades = []

    # Entradas de mercancía del día
    entradas = EntradaInsumo.objects.filter(creado_en__gte=inicio_hoy)
    # ── FILTRO DINÁMICO ──
    if sucursal:
        entradas = entradas.filter(sucursal=sucursal)

    for e in entradas.order_by('creado_en')[:5]:
        actividades.append({
            'type':        'entrada',
            'descripcion': f'Entrada de Mercancía: {e.producto} — {e.cantidad} {e.unidad}',
            'hora':        e.creado_en,
        })

    # Ventas procesadas como referencia de actividad
    pedidos = Pedido.objects.filter(
        creado_en__gte = inicio_hoy,
        estado__in     = ['procesado', 'procesada', 'COMPLETADA', 'completado'],
    )
    # ── FILTRO DINÁMICO ──
    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    total_ventas_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0')
    if total_ventas_dia > 0:
        actividades.append({
            'type':        'validacion',
            'descripcion': f'Ventas del día registradas: ${total_ventas_dia:,.2f} en {pedidos.count()} pedidos',
            'hora':        ahora,
        })

    # Cortes anteriores del día (Usa fecha nativa de CierreCaja)
    cortes_hoy = CierreCaja.objects.filter(fecha=ahora.date())
    # ── FILTRO DINÁMICO ──
    if sucursal:
        cortes_hoy = cortes_hoy.filter(sucursal=sucursal)

    for c in cortes_hoy:
        # Corrección del objeto combinado de tiempo para el ordenamiento analítico
        hora_actividad = ahora
        if c.fecha and c.hora_cierre:
            try:
                hora_actividad = datetime.combine(c.fecha, c.hora_cierre)
                if timezone.is_naive(hora_actividad):
                    hora_actividad = timezone.make_aware(hora_actividad)
            except Exception:
                hora_actividad = ahora

        actividades.append({
            'type':        'retiro',
            'descripcion': f'Cierre de turno previo: {c.get_turno_display()} — ${c.efectivo_real:,.2f}',
            'hora':        hora_actividad,
        })

    # Ordena por hora de forma segura comprobando la existencia de atributos nativos
    actividades.sort(key=lambda x: x['hora'] if x['hora'] else ahora)
    return actividades


@login_required(login_url='/')
@gerente_o_superior
def cierre_caja_view(request):
    # ── INTEGRACIÓN DEL SELECTOR GLOBAL OFICIAL ──
    sucursal      = get_sucursal_contexto(request)
    ahora         = timezone.now()
    fondo_inicial = Decimal('200.00')

    # ── Datos reales de ventas del día ────────────────
    datos_ventas    = _calcular_ventas_dia(sucursal)
    ventas_efectivo = datos_ventas['ventas_efectivo']
    ventas_tarjeta  = datos_ventas['ventas_tarjeta']
    ventas_delivery = datos_ventas['ventas_delivery']
    total_ventas    = datos_ventas['total_ventas']
    num_pedidos     = datos_ventas['num_pedidos']
    total_esperado  = fondo_inicial + ventas_efectivo

    # ── Actividades del turno ─────────────────────────
    actividades = _calcular_actividades_turno(sucursal)

    # ── Últimos cortes (historial con campos reales) ──
    ultimos_cortes = CierreCaja.objects.select_related('usuario', 'sucursal').order_by('-fecha', '-hora_cierre')
    # ── FILTRO DINÁMICO ──
    if sucursal:
        ultimos_cortes = ultimos_cortes.filter(sucursal=sucursal)
    ultimos_cortes = ultimos_cortes[:3]

    # ── Turno detectado automáticamente ───────────────
    hora_actual = ahora.hour
    if 6 <= hora_actual < 14:
        turno_auto = 'matutino'
    elif 14 <= hora_actual < 22:
        turno_auto = 'vespertino'
    else:
        turno_auto = 'nocturno'

    # ── Procesar el formulario ────────────────────────
    if request.method == 'POST':
        # Bloqueo adicional de seguridad: No se puede cerrar caja en "Todas las Sucursales"
        if not sucursal:
            messages.warning(request, "⚠️ Para realizar un cierre de caja, debes seleccionar una sucursal específica en el menú superior.")
            return redirect('CierreCaja:cierre')
            
        form = CierreCajaForm(request.POST)
        if form.is_valid():
            cierre                 = form.save(commit=False)
            cierre.usuario         = request.user
            cierre.sucursal        = sucursal
            cierre.ventas_efectivo = ventas_efectivo
            cierre.ventas_tarjeta  = ventas_tarjeta
            cierre.ventas_delivery = ventas_delivery
            cierre.fondo_inicial   = fondo_inicial
            cierre.save()

            dif = cierre.diferencia
            if dif == 0:
                messages.success(
                    request,
                    f'✅ Turno cerrado correctamente. Sin diferencia en caja.'
                )
            elif dif > 0:
                messages.success(
                    request,
                    f'✅ Turno cerrado. Sobrante de caja: +${dif:,.2f}'
                )
            else:
                messages.warning(
                    request,
                    f'⚠️ Turno cerrado. Faltante de caja: ${dif:,.2f}'
                )
            return redirect('CierreCaja:cierre')
        else:
            messages.error(request, '❌ Revisa los campos marcados.')
    else:
        form = CierreCajaForm(initial={
            'turno':          turno_auto,
            'fondo_inicial':  fondo_inicial,
        })

    context = {
        'form':             form,
        'ventas_efectivo':  ventas_efectivo,
        'ventas_tarjeta':   ventas_tarjeta,
        'ventas_delivery':  ventas_delivery,
        'total_ventas':     total_ventas,
        'num_pedidos':      num_pedidos,
        'fondo_inicial':    fondo_inicial,
        'total_esperado':   total_esperado,
        'turno_auto':       turno_auto,
        'actividades':      actividades,
        'ultimos_cortes':   ultimos_cortes,
        'fecha_actual':     ahora.strftime('%d %b, %Y'),
        'hora_actual':      ahora.strftime('%H:%M'),
        # Ya no pasamos 'sucursal_actual' porque context_processor.py lo maneja globalmente
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'CierreCaja/CierreCaja.html', context)





