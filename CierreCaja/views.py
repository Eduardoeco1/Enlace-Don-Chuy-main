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
    from Ventas.models import Pedido

    hoy = timezone.now().date()

    pedidos = Pedido.objects.filter(
        creado_en__date=hoy,
        estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
    )

    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    total_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    num_pedidos = pedidos.count()

    ventas_efectivo = Decimal('0.00')
    ventas_tarjeta = Decimal('0.00')

    metodos_pago = pedidos.values('metodo_pago').annotate(total=Sum('total'))

    for metodo in metodos_pago:
        nombre_metodo = str(metodo['metodo_pago']).lower().strip() if metodo['metodo_pago'] else ''
        monto = metodo['total'] or Decimal('0.00')

        if nombre_metodo == 'efectivo':
            ventas_efectivo = monto
        elif nombre_metodo == 'tarjeta':
            ventas_tarjeta = monto

    return {
        'ventas_efectivo': ventas_efectivo,
        'ventas_tarjeta': ventas_tarjeta,
        'total_ventas': total_dia,
        'num_pedidos': num_pedidos,
    }


def _calcular_actividades_turno(sucursal=None):
    from EntradaMercancia.models import EntradaInsumo
    from Ventas.models import Pedido

    ahora = timezone.now()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    actividades = []

    entradas = EntradaInsumo.objects.filter(creado_en__gte=inicio_hoy)

    if sucursal:
        entradas = entradas.filter(sucursal=sucursal)

    for e in entradas.order_by('-creado_en')[:5]:
        actividades.append({
            'type': 'entrada',
            'descripcion': f'Entrada de Mercancía: {e.producto} — {e.cantidad} {e.unidad}',
            'hora': e.creado_en,
        })

    pedidos = Pedido.objects.filter(
        creado_en__gte=inicio_hoy,
        estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado'],
    )

    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)

    total_ventas_dia = pedidos.aggregate(t=Sum('total'))['t'] or Decimal('0.00')

    if total_ventas_dia > 0:
        actividades.append({
            'type': 'validacion',
            'descripcion': f'Ventas del día registradas: ${total_ventas_dia:,.2f} en {pedidos.count()} pedidos',
            'hora': ahora,
        })

    cortes_hoy = CierreCaja.objects.filter(fecha=ahora.date())

    if sucursal:
        cortes_hoy = cortes_hoy.filter(sucursal=sucursal)

    for cierre in cortes_hoy:
        hora_actividad = ahora

        if cierre.fecha and cierre.hora_cierre:
            try:
                hora_actividad = datetime.combine(cierre.fecha, cierre.hora_cierre)

                if timezone.is_naive(hora_actividad):
                    hora_actividad = timezone.make_aware(hora_actividad)

            except Exception:
                hora_actividad = ahora

        actividades.append({
            'type': 'retiro',
            'descripcion': f'Cierre previo: {cierre.get_turno_display()} — ${cierre.efectivo_real:,.2f}',
            'hora': hora_actividad,
        })

    def normalizar_fecha(valor):
        if not valor:
            return ahora

        if isinstance(valor, datetime):
            if timezone.is_naive(valor):
                return timezone.make_aware(valor)
            return valor

        return ahora

    actividades.sort(
        key=lambda x: normalizar_fecha(x.get('hora')),
        reverse=True
    )

    return actividades


@login_required(login_url='/')
@gerente_o_superior
def cierre_caja_view(request):
    sucursal = get_sucursal_contexto(request)
    ahora = timezone.now()

    fondo_inicial = Decimal('200.00')
    turno_seleccionado = request.GET.get('turno', 'todos')

    datos_ventas = _calcular_ventas_dia(sucursal)

    ventas_efectivo = datos_ventas['ventas_efectivo']
    ventas_tarjeta = datos_ventas['ventas_tarjeta']
    total_ventas = datos_ventas['total_ventas']
    num_pedidos = datos_ventas['num_pedidos']

    actividades = _calcular_actividades_turno(sucursal)

    ultimos_cortes = CierreCaja.objects.select_related(
        'usuario',
        'sucursal'
    ).order_by('-fecha', '-hora_cierre')

    if sucursal:
        ultimos_cortes = ultimos_cortes.filter(sucursal=sucursal)

    if turno_seleccionado != 'todos':
        ultimos_cortes = ultimos_cortes.filter(turno=turno_seleccionado)

    ultimos_cortes = ultimos_cortes[:3]

    hora_actual = ahora.hour

    if 6 <= hora_actual < 14:
        turno_auto = 'matutino'
    else:
        turno_auto = 'vespertino'

    if request.method == 'POST':

        if not sucursal:
            messages.warning(request, '⚠️ Debes seleccionar una sucursal.')
            return redirect('CierreCaja:cierre')

        form = CierreCajaForm(request.POST)

        if form.is_valid():
            cierre = form.save(commit=False)

            cierre.usuario = request.user
            cierre.sucursal = sucursal
            cierre.ventas_efectivo = ventas_efectivo
            cierre.ventas_tarjeta = ventas_tarjeta
            cierre.fondo_inicial = fondo_inicial

            cierre.save()

            dif = cierre.diferencia

            if dif == 0:
                messages.success(request, '✅ Turno cerrado correctamente.')
            elif dif > 0:
                messages.success(request, f'✅ Sobrante detectado: +${dif:,.2f}')
            else:
                messages.warning(request, f'⚠️ Faltante detectado: ${dif:,.2f}')

            return redirect('CierreCaja:cierre')

        else:
            messages.error(request, '❌ Revisa los campos marcados.')

    else:
        form = CierreCajaForm(initial={
            'turno': turno_auto,
            'fondo_inicial': fondo_inicial,
        })

    context = {
        'form': form,
        'ventas_efectivo': ventas_efectivo,
        'ventas_tarjeta': ventas_tarjeta,
        'total_ventas': total_ventas,
        'num_pedidos': num_pedidos,
        'fondo_inicial': fondo_inicial,
        'turno_auto': turno_auto,
        'turno_seleccionado': turno_seleccionado,
        'actividades': actividades,
        'ultimos_cortes': ultimos_cortes,
        'fecha_actual': ahora.strftime('%d %b, %Y'),
        'hora_actual': ahora.strftime('%H:%M'),
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'CierreCaja/CierreCaja.html', context)


