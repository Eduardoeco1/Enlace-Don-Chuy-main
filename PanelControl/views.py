import pytz
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, F, Avg

# ── IMPORTAMOS EL SELECTOR GLOBAL OFICIAL ──
from Sucursales.permisos import get_sucursal_contexto, cualquier_rol

# Importación de Modelos
from Ventas.models import Pedido, DetallePedido
from Inventario.models import Producto as ProductoInventario
from PanelControl.utils import generar_sugerencia
from CierreCaja.models import CierreCaja

# Metas Diarias
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
    # ── INTEGRACIÓN DEL SELECTOR GLOBAL OFICIAL ──
    sucursal = get_sucursal_contexto(request)
    
    # Usar la hora local (CDMX) para evitar desfases con UTC
    ahora_local = timezone.now()
    inicio      = ahora_local.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_ayer = inicio - timedelta(days=1)

    # ── Ventas del día filtradas por sucursal ─────────
    ventas_qs = Pedido.objects.filter(
        creado_en__gte=inicio, 
        estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
    )
    if sucursal:
        ventas_qs = ventas_qs.filter(sucursal=sucursal)

    ventas_totales  = ventas_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')
    volumen_ordenes = ventas_qs.count()

    # Variación vs ayer
    ayer_qs = Pedido.objects.filter(
        creado_en__gte=inicio_ayer,
        creado_en__lt=inicio, 
        estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
    )
    if sucursal:
        ayer_qs = ayer_qs.filter(sucursal=sucursal)

    ventas_ayer = ayer_qs.aggregate(t=Sum('total'))['t'] or Decimal('0')
    if ventas_ayer > 0:
        variacion_pct = ((ventas_totales - ventas_ayer) / ventas_ayer) * 100
        signo         = '+' if variacion_pct >= 0 else ''
        ventas_variacion = f'{signo}{variacion_pct:.1f}% vs ayer'
    else:
        ventas_variacion = 'Sin datos de ayer'

    # Progreso calculado sobre la meta de VENTAS
    progreso_meta = min(int((ventas_totales / META_DIARIA_VENTAS) * 100), 100)
    
    ticket_promedio = (f'{ventas_totales / volumen_ordenes:,.2f}/ticket'
                       if volumen_ordenes > 0 else '0.00/ticket')

    # ── Más vendidos (Métricas consistentes agrupadas) ───
    detalles_qs = DetallePedido.objects.filter(
        pedido__creado_en__gte=inicio,
        pedido__estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
    )
    if sucursal:
        detalles_qs = detalles_qs.filter(pedido__sucursal=sucursal)

    top_raw = (
        detalles_qs
        .values('producto__id', 'producto__nombre')
        .annotate(
            total_vendidos=Sum('cantidad'), 
            total_ingreso=Sum(F('cantidad') * F('precio_u'))
        )
        .order_by('-total_ingreso')[:3]
    )

    productos_top = []
    for item in top_raw:
        try:
            prod = ProductoInventario.objects.get(pk=item['producto__id'])
            img  = prod.get_imagen() if hasattr(prod, 'get_imagen') else ''
        except ProductoInventario.DoesNotExist:
            img = 'https://placehold.co/48x48/f0eded/904800?text=LC'
        
        productos_top.append({
            'nombre':   item['producto__nombre'],
            'vendidos': item['total_vendidos'] or 0,
            'total':    f"{item['total_ingreso']:,.2f}" if item['total_ingreso'] else "0.00",
            'imagen':   img,
        })

    # ── Asientos recientes filtrados por sucursal ─────
    ventas_rec = (
        Pedido.objects
        .filter(creado_en__gte=inicio, estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado'])
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
    
    # Procesar ventas recientes
    for v in ventas_rec:
        detalles_lista = list(v.detalles.all())
        desc = detalles_lista[0] if detalles_lista else None
        
        asientos_raw.append({
            'referencia':     v.ticket or f'#TX-{v.pk}',
            'descripcion':    f'Venta — {desc.producto.nombre}' if desc else 'Venta',
            'tipo':           'VENTA',
            'monto':          f'${v.total:,.2f}',
            'monto_negativo': False,
            'timestamp':      v.creado_en,
        })
        
    # Procesar closures de caja recientes
    for s in salidas_rec:
        dt_cierre = datetime.combine(s.fecha, s.hora_cierre)
        if timezone.is_aware(ahora_local): 
            dt_cierre = timezone.make_aware(dt_cierre, ahora_local.tzinfo)

        asientos_raw.append({
            'referencia':     f'#CC-{s.pk}',
            'descripcion':    f'Cierre {s.get_turno_display()}',
            'tipo':           'GASTO',
            'monto':          f'-${s.efectivo_real:,.2f}',
            'monto_negativo': True,
            'timestamp':      dt_cierre,
        })

    # Ordenar por timestamp real
    asientos_raw.sort(key=lambda x: x['timestamp'], reverse=True)

    # Formatear la respuesta final de la tabla
    asientos = []
    for a in asientos_raw[:5]:
        asientos.append({
            'referencia':     a['referencia'],
            'descripcion':    a['descripcion'],
            'tipo':           a['tipo'],
            'monto':          a['monto'],
            'monto_negativo': a['monto_negativo'],
            'hora':           a['timestamp'].strftime('%H:%M'),
        })

    # ── NUEVA IMPLEMENTACIÓN: Tendencia de Ventas (Últimas 24 Horas) ──
    tendencia = []
    # Generamos 6 bloques de 4 horas cada uno para cubrir las 24h
    for i in range(5, -1, -1):
        inicio_bloque = ahora_local - timedelta(hours=(i+1)*4)
        fin_bloque    = ahora_local - timedelta(hours=i*4)

        pedidos_bloque = Pedido.objects.filter(
            creado_en__gte=inicio_bloque,
            creado_en__lt=fin_bloque,
            estado__in=['procesado', 'procesada', 'COMPLETADA', 'completado']
        )
        if sucursal:
            pedidos_bloque = pedidos_bloque.filter(sucursal=sucursal)

        total_bloque = pedidos_bloque.aggregate(t=Sum('total'))['t'] or Decimal('0')
        
        tendencia.append({
            'hora': fin_bloque.strftime('%H:%M'),
            'total': total_bloque,
            'porcentaje': 0  # Se calcula en el siguiente paso
        })

    # Calcular porcentajes relativos para las alturas de las columnas de Tailwind
    max_venta_bloque = max([item['total'] for item in tendencia]) if tendencia else Decimal('0')
    for item in tendencia:
        if max_venta_bloque > 0:
            # Escalamos la barra entre el 8% (mínimo visual) y el 100% (el bloque con más ventas)
            item['porcentaje'] = int((item['total'] / max_venta_bloque) * 92) + 8
        else:
            item['porcentaje'] = 8  # Altura base decorativa si no hay ventas

    # ── Sugerencia inteligente filtrada ───────────────
    try:
        sugerencia = generar_sugerencia(ProductoInventario, Pedido, sucursal=sucursal)
    except TypeError:
        sugerencia = generar_sugerencia(ProductoInventario, Pedido)

    context = {
        'saludo':           _get_saludo_cdmx(),
        'ventas_totales':   f'{ventas_totales:,.2f}',
        'ventas_variacion': ventas_variacion,
        'volumen_ordenes':  volumen_ordenes,
        'meta_diaria':      f'{META_DIARIA_VENTAS:,.2f}', 
        'progreso_meta':    progreso_meta,
        'ticket_promedio':  ticket_promedio,
        'mas_vendidos':     productos_top,
        'asientos':         asientos,
        'sugerencia':       sugerencia,
        'tendencia':        tendencia,
        # 'sucursal_actual' ya no hace falta pasarlo aquí, el context_processor lo manda al HTML.
        'usuario_nombre':   request.user.get_full_name() or request.user.username,
    }
    return render(request, 'PanelControl/PanelControl.html', context)









