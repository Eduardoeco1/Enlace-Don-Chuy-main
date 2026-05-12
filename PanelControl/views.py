import pytz
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, Avg

from Ventas.models import Pedido, DetallePedido
from Ventas.models import Producto as ProductoVenta
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto
from PanelControl.utils import generar_sugerencia

META_DIARIA_ORDENES = 200
META_DIARIA_VENTAS  = Decimal('50000.00')

def _get_saludo_cdmx():
    """Saludo según hora actual de Ciudad de México."""
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
def panel_view(request):
    sucursal = get_sucursal_contexto(request)
    ahora    = timezone.now()
    inicio   = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_ayer = inicio - timedelta(days=1)

    # ── Ventas del día filtradas por sucursal ─────────
    ventas_qs = Pedido.objects.filter(creado_en__gte=inicio, estado='procesado')
    if sucursal:
        ventas_qs = ventas_qs.filter(sucursal=sucursal)

    ventas_totales  = ventas_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')
    volumen_ordenes = ventas_qs.count()

    # Variación vs ayer
    ayer_qs       = Pedido.objects.filter(creado_en__gte=inicio_ayer,
                                          creado_en__lt=inicio, estado='procesado')
    if sucursal:
        ayer_qs = ayer_qs.filter(sucursal=sucursal)

    ventas_ayer   = ayer_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')
    if ventas_ayer > 0:
        variacion_pct = ((ventas_totales - ventas_ayer) / ventas_ayer) * 100
        signo         = '+' if variacion_pct >= 0 else ''
        ventas_variacion = f'{signo}{variacion_pct:.1f}% vs ayer'
    else:
        ventas_variacion = 'Sin datos de ayer'

    progreso_meta   = min(int((ventas_totales / META_DIARIA_VENTAS) * 100), 100)
    ticket_promedio = (f'${ventas_totales / volumen_ordenes:,.2f}/ticket'
                       if volumen_ordenes > 0 else '$0/ticket')

    # ── Más vendidos filtrados por sucursal ───────────
    detalles_qs = DetallePedido.objects.filter(pedido__creado_en__gte=inicio,
                                               pedido__estado='procesado')
    if sucursal:
        detalles_qs = detalles_qs.filter(pedido__sucursal=sucursal)

    top_raw = (
        detalles_qs
        .select_related('producto')
        .values('producto__id', 'producto__nombre', 'producto__imagen_url')
        .annotate(total_vendidos=Count('cantidad'), total_ingreso=Sum('subtotal'))
        .order_by('-total_ingreso')[:3]
    )

    productos_top = []
    for item in top_raw:
        try:
            prod = ProductoVenta.objects.get(pk=item['producto__id'])
            img  = prod.get_imagen()
        except ProductoVenta.DoesNotExist:
            img = 'https://placehold.co/48x48/f0eded/904800?text=LC'
        productos_top.append({
            'nombre':   item['producto__nombre'],
            'vendidos': item['total_vendidos'],
            'total':    f"${item['total_ingreso']:,.2f}",
            'imagen':   img,
        })

    # ── Asientos recientes filtrados por sucursal ─────
    from Ventas.models import Pedido as PedidoVenta
    from CierreCaja.models import CierreCaja

    ventas_rec = (
        PedidoVenta.objects
        .filter(creado_en__gte=inicio, estado='procesado')
        .prefetch_related('detalles__producto')
        .order_by('-creado_en')
    )
    if sucursal:
        ventas_rec = ventas_rec.filter(sucursal=sucursal)
    ventas_rec = ventas_rec[:5]

    salidas_rec = CierreCaja.objects.filter(
        fecha=ahora.date()
    ).order_by('-hora_cierre')
    
    if sucursal:
        salidas_rec = salidas_rec.filter(sucursal=sucursal)
    salidas_rec = salidas_rec[:5]

    asientos = []
    for v in ventas_rec:
        desc = v.detalles.first()
        asientos.append({
            'referencia':     v.ticket or f'#TX-{v.pk}',
            'descripcion':    f'Venta — {desc.producto.nombre}' if desc else 'Venta',
            'tipo':           'VENTA',
            'monto':          f'${v.total:,.2f}',
            'monto_negativo': False,
            'hora':           v.creado_en.strftime('%H:%M'),
        })
    for s in salidas_rec:
        asientos.append({
            'referencia':     f'#CC-{s.pk}',
            'descripcion':    f'Cierre {s.get_turno_display()}',
            'tipo':           'GASTO',
            'monto':          f'-${s.efectivo_real:,.2f}',
            'monto_negativo': True,
            'hora':           s.hora_cierre.strftime('%H:%M'),
        })
    asientos.sort(key=lambda x: x['hora'], reverse=True)

    # ── Sugerencia inteligente filtrada ───────────────
    from Ventas.models import Producto as ProdVenta
    sugerencia = generar_sugerencia(ProdVenta, PedidoVenta)

    context = {
        'saludo':           _get_saludo_cdmx(),
        'ventas_totales':   f'{ventas_totales:,.2f}',
        'ventas_variacion': ventas_variacion,
        'volumen_ordenes':  volumen_ordenes,
        'meta_diaria':      META_DIARIA_ORDENES,
        'progreso_meta':    progreso_meta,
        'ticket_promedio':  ticket_promedio,
        'mas_vendidos':     productos_top,
        'asientos':         asientos[:5],
        'sugerencia':       sugerencia,
        'sucursal_actual':  sucursal,
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'PanelControl/PanelControl.html', context)





