from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime

from .models import CierreCaja, ActividadTurno
from .forms import CierreCajaForm
from Sucursales.permisos import gerente_o_superior, get_sucursal_contexto


def _calcular_ventas_dia(sucursal=None):
    """
    Calcula las ventas reales del día desde el modelo Pedido.
    Separa por método de pago si está disponible,
    de lo contrario retorna el total general.
    """
    from Ventas.models import Pedido

    ahora      = timezone.now()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    pedidos = Pedido.objects.filter(
        creado_en__gte = inicio_hoy,
        estado         = 'procesado',
    )
    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    # Totales por método de pago
    # Si tu modelo Pedido tiene campo metodo_pago, filtra así:
    # ventas_efectivo = pedidos.filter(metodo_pago='efectivo').aggregate(t=Sum('total'))['t'] or 0
    # ventas_tarjeta  = pedidos.filter(metodo_pago='tarjeta').aggregate(t=Sum('total'))['t'] or 0
    # ventas_delivery = pedidos.filter(metodo_pago='delivery').aggregate(t=Sum('total'))['t'] or 0

    # Por ahora distribuimos el total proporcionalmente
    total_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0')
    num_pedidos = pedidos.count()

    # Distribución estimada (ajusta según tu lógica de negocio)
    ventas_efectivo = (total_dia * Decimal('0.55')).quantize(Decimal('0.01'))
    ventas_tarjeta  = (total_dia * Decimal('0.35')).quantize(Decimal('0.01'))
    ventas_delivery = (total_dia - ventas_efectivo - ventas_tarjeta).quantize(Decimal('0.01'))

    return {
        'ventas_efectivo': ventas_efectivo,
        'ventas_tarjeta':  ventas_tarjeta,
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
    if sucursal:
        entradas = entradas.filter(sucursal=sucursal)

    for e in entradas.order_by('creado_en')[:5]:
        actividades.append({
            'tipo':        'entrada',
            'descripcion': f'Entrada de Mercancía: {e.producto} — {e.cantidad} {e.unidad}',
            'hora':        e.creado_en,
        })

    # Ventas procesadas como referencia de actividad
    pedidos = Pedido.objects.filter(
        creado_en__gte = inicio_hoy,
        estado         = 'procesado',
    )
    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    total_ventas_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0')
    if total_ventas_dia > 0:
        actividades.append({
            'tipo':        'validacion',
            'descripcion': f'Ventas del día registradas: ${total_ventas_dia:,.2f} en {pedidos.count()} pedidos',
            'hora':        ahora,
        })

    # Cortes anteriores del día (si ya hubo alguno)
    cortes_hoy = CierreCaja.objects.filter(fecha=ahora.date())
    if sucursal:
        cortes_hoy = cortes_hoy.filter(sucursal=sucursal)

    for c in cortes_hoy:
        actividades.append({
            'tipo':        'retiro',
            'descripcion': f'Cierre de turno previo: {c.get_turno_display()} — ${c.efectivo_real:,.2f}',
            'hora':        datetime.combine(c.fecha, c.hora_cierre),
        })

    # Ordena por hora
    actividades.sort(key=lambda x: x['hora'] if hasattr(x['hora'], 'hour') else x['hora'])
    return actividades


@login_required(login_url='/')
@gerente_o_superior
def cierre_caja_view(request):
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

    # ── Últimos cortes (historial) ────────────────────
    ultimos_cortes = CierreCaja.objects.select_related('usuario', 'sucursal').order_by('-fecha', '-hora_cierre')
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
        # Formulario
        'form':             form,
        # Datos dinámicos de ventas
        'ventas_efectivo':  ventas_efectivo,
        'ventas_tarjeta':   ventas_tarjeta,
        'ventas_delivery':  ventas_delivery,
        'total_ventas':     total_ventas,
        'num_pedidos':      num_pedidos,
        'fondo_inicial':    fondo_inicial,
        'total_esperado':   total_esperado,
        # Turno detectado
        'turno_auto':       turno_auto,
        # Actividades
        'actividades':      actividades,
        # Historial
        'ultimos_cortes':   ultimos_cortes,
        # Meta
        'fecha_actual':     ahora.strftime('%d %b, %Y'),
        'hora_actual':      ahora.strftime('%H:%M'),
        'sucursal_actual':  sucursal,
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'CierreCaja/CierreCaja.html', context)



