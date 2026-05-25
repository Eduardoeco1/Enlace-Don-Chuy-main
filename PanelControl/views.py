import pytz
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F

from Sucursales.permisos import get_sucursal_contexto, cualquier_rol
from Ventas.models import Pedido, DetallePedido
from Inventario.models import Producto as ProductoInventario
from PanelControl.utils import generar_sugerencia
from CierreCaja.models import CierreCaja
from Reportes.models import MetaSemanal


ESTADOS_VALIDOS = ['procesado', 'procesada', 'COMPLETADA', 'completado']


def _get_saludo_cdmx():
    tz_cdmx = pytz.timezone('America/Mexico_City')
    hora = datetime.now(tz_cdmx).hour

    if 6 <= hora < 12:
        return 'Buenos días'
    elif 12 <= hora < 19:
        return 'Buenas tardes'
    return 'Buenas noches'


def normalizar_timestamp(valor):
    if not valor:
        return timezone.now()

    if timezone.is_naive(valor):
        return timezone.make_aware(valor)

    return valor


@login_required(login_url='/')
@cualquier_rol
def panel_view(request):
    sucursal = get_sucursal_contexto(request)

    ahora_local = timezone.now()
    inicio = ahora_local.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_ayer = inicio - timedelta(days=1)

    ventas_qs = Pedido.objects.filter(
        creado_en__gte=inicio,
        estado__in=ESTADOS_VALIDOS
    )

    if sucursal:
        ventas_qs = ventas_qs.filter(sucursal=sucursal)

    ventas_totales = ventas_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')
    volumen_ordenes = ventas_qs.count()

    ayer_qs = Pedido.objects.filter(
        creado_en__gte=inicio_ayer,
        creado_en__lt=inicio,
        estado__in=ESTADOS_VALIDOS
    )

    if sucursal:
        ayer_qs = ayer_qs.filter(sucursal=sucursal)

    ventas_ayer = ayer_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')

    if ventas_ayer > 0:
        variacion_pct = ((ventas_totales - ventas_ayer) / ventas_ayer) * 100
        signo = '+' if variacion_pct >= 0 else ''
        ventas_variacion = f'{signo}{variacion_pct:.1f}% vs ayer'
    else:
        ventas_variacion = 'Sin datos de ayer'

    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    meta_obj = MetaSemanal.objects.filter(
        sucursal=sucursal,
        fecha_inicio=inicio_semana
    ).first()

    objetivo_meta = meta_obj.objetivo_monto if meta_obj else Decimal('50000.00')

    progreso_meta = min(
        int((ventas_totales / objetivo_meta) * 100),
        100
    ) if objetivo_meta > 0 else 0

    ticket_promedio = (
        f'{ventas_totales / volumen_ordenes:,.2f}/ticket'
        if volumen_ordenes > 0
        else '0.00/ticket'
    )

    pedidos_ids_hoy = ventas_qs.values_list('id', flat=True)

    detalles_qs = DetallePedido.objects.filter(
    pedido_id__in=pedidos_ids_hoy
)
    top_raw = (
        detalles_qs
        .values('producto__id', 'producto__nombre')
        .annotate(
            total_vendidos=Sum('cantidad'),
            total_ingreso=Sum('subtotal')
        )
        .order_by('-total_ingreso')[:3]
    )

    productos_top = []

    for item in top_raw:
        try:
            prod = ProductoInventario.objects.get(pk=item['producto__id'])
            img = prod.get_imagen() if hasattr(prod, 'get_imagen') else ''
        except ProductoInventario.DoesNotExist:
            img = 'https://placehold.co/48x48/f0eded/904800?text=ED'

        productos_top.append({
            'nombre': item['producto__nombre'],
            'vendidos': item['total_vendidos'] or 0,
            'total': f"{item['total_ingreso']:,.2f}" if item['total_ingreso'] else "0.00",
            'imagen': img,
        })

    ventas_rec = (
        Pedido.objects
        .filter(creado_en__gte=inicio, estado__in=ESTADOS_VALIDOS)
        .prefetch_related('detalles__producto')
        .order_by('-creado_en')
    )

    if sucursal:
        ventas_rec = ventas_rec.filter(sucursal=sucursal)

    ventas_rec = ventas_rec[:5]

    salidas_rec = CierreCaja.objects.filter(
        fecha=ahora_local.date()
    ).order_by('-hora_cierre')

    if sucursal:
        salidas_rec = salidas_rec.filter(sucursal=sucursal)

    salidas_rec = salidas_rec[:5]

    asientos_raw = []

    for v in ventas_rec:
        detalles_lista = list(v.detalles.all())
        desc = detalles_lista[0] if detalles_lista else None

        asientos_raw.append({
            'referencia': v.ticket or f'#TX-{v.pk}',
            'descripcion': f'Venta — {desc.producto.nombre}' if desc else 'Venta',
            'tipo': 'VENTA',
            'monto': f'${v.total:,.2f}',
            'monto_negativo': False,
            'timestamp': v.creado_en,
        })

    for s in salidas_rec:
        dt_cierre = datetime.combine(s.fecha, s.hora_cierre)

        if timezone.is_naive(dt_cierre):
            dt_cierre = timezone.make_aware(dt_cierre)

        asientos_raw.append({
            'referencia': f'#CC-{s.pk}',
            'descripcion': f'Cierre {s.get_turno_display()}',
            'tipo': 'CORTE',
            'monto': f'${s.efectivo_real:,.2f}',
            'monto_negativo': False,
            'timestamp': dt_cierre,
        })

    asientos_raw.sort(
        key=lambda x: normalizar_timestamp(x['timestamp']),
        reverse=True
    )

    asientos = []

    for a in asientos_raw[:5]:
        timestamp = normalizar_timestamp(a['timestamp'])

        asientos.append({
            'referencia': a['referencia'],
            'descripcion': a['descripcion'],
            'tipo': a['tipo'],
            'monto': a['monto'],
            'monto_negativo': a['monto_negativo'],
            'hora': timestamp.strftime('%H:%M'),
        })

    tendencia = []

    for i in range(5, -1, -1):
        inicio_bloque = ahora_local - timedelta(hours=(i + 1) * 4)
        fin_bloque = ahora_local - timedelta(hours=i * 4)

        pedidos_bloque = Pedido.objects.filter(
            creado_en__gte=inicio_bloque,
            creado_en__lt=fin_bloque,
            estado__in=ESTADOS_VALIDOS
        )

        if sucursal:
            pedidos_bloque = pedidos_bloque.filter(sucursal=sucursal)

        total_bloque = pedidos_bloque.aggregate(t=Sum('total'))['t'] or Decimal('0')

        tendencia.append({
            'hora': fin_bloque.strftime('%H:%M'),
            'total': total_bloque,
            'porcentaje': 0,
        })

    max_venta_bloque = max([item['total'] for item in tendencia]) if tendencia else Decimal('0')

    for item in tendencia:
        if max_venta_bloque > 0:
            item['porcentaje'] = int((item['total'] / max_venta_bloque) * 92) + 8
        else:
            item['porcentaje'] = 8

    try:
        sugerencia = generar_sugerencia(ProductoInventario, Pedido, sucursal=sucursal)
    except TypeError:
        sugerencia = generar_sugerencia(ProductoInventario, Pedido)

    context = {
        'saludo': _get_saludo_cdmx(),
        'ventas_totales': f'{ventas_totales:,.2f}',
        'ventas_variacion': ventas_variacion,
        'volumen_ordenes': volumen_ordenes,
        'objetivo_meta': f'{objetivo_meta:,.2f}',
        'progreso_meta': progreso_meta,
        'ticket_promedio': ticket_promedio,
        'mas_vendidos': productos_top,
        'asientos': asientos,
        'sugerencia': sugerencia,
        'tendencia': tendencia,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'PanelControl/PanelControl.html', context)