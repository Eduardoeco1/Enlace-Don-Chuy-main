import csv
from decimal import Decimal
from datetime import timedelta

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Avg, F
from django.template.loader import get_template

from xhtml2pdf import pisa

from Ventas.models import Pedido
from CierreCaja.models import CierreCaja
from Reportes.models import Insumo, MetaSemanal
from Sucursales.permisos import gerente_o_superior, get_sucursal_contexto

def _get_contexto_reporte(request):
    sucursal    = get_sucursal_contexto(request)
    ahora       = timezone.now()
    inicio_sem  = ahora - timedelta(days=7)
    inicio_sem_ant = ahora - timedelta(days=14)

    # ── Base queryset filtrada por sucursal ───────────
    pedidos_qs = Pedido.objects.filter(estado='procesado')
    if sucursal:
        pedidos_qs = pedidos_qs.filter(sucursal=sucursal)

    # Ventas actuales vs anteriores
    ventas_semana  = pedidos_qs.filter(creado_en__gte=inicio_sem)
    ventas_sem_ant = pedidos_qs.filter(creado_en__gte=inicio_sem_ant, creado_en__lt=inicio_sem)

    total_semana  = ventas_semana.aggregate(t=Sum('total'))['t'] or Decimal('0')
    total_sem_ant = ventas_sem_ant.aggregate(t=Sum('total'))['t'] or Decimal('0')
    ticket_prom   = ventas_semana.aggregate(a=Avg('total'))['a'] or Decimal('0')
    num_ventas    = ventas_semana.count()

    if total_sem_ant > 0:
        variacion = ((total_semana - total_sem_ant) / total_sem_ant) * 100
        variacion_txt = f'+{variacion:.1f}%' if variacion >= 0 else f'{variacion:.1f}%'
    else:
        variacion_txt = 'Sin datos anteriores'

    # ── Meta semanal ──────────────────────────────────
    meta_qs = MetaSemanal.objects.order_by('-fecha_inicio')
    if sucursal:
        meta_qs = meta_qs.filter(sucursal=sucursal)
    
    meta     = meta_qs.first()
    objetivo = meta.objetivo_monto if meta else Decimal('175000')
    progreso = min(int((total_semana / objetivo) * 100), 100)

    # ── Ventas por día ────────────────────────────────
    ventas_por_dia = []
    labels_dias    = []
    dias_semana    = ['LUN','MAR','MIÉ','JUE','VIE','SÁB','DOM']

    for i in range(6, -1, -1):
        dia   = ahora - timedelta(days=i)
        ini   = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        fin   = ini + timedelta(days=1)
        qs_d  = pedidos_qs.filter(creado_en__gte=ini, creado_en__lt=fin)
        total_d = qs_d.aggregate(t=Sum('total'))['t'] or 0
        ventas_por_dia.append(float(total_d))
        labels_dias.append(dias_semana[dia.weekday()])

    # ── Discrepancias de inventario ───────────────────
    disc_qs = Insumo.objects.filter(stock_fisico__lt=F('stock_esperado'))
    if sucursal:
        disc_qs = disc_qs.filter(sucursal=sucursal)
    discrepancias = disc_qs.order_by('stock_fisico')[:10]

    # ── Últimos cierres ───────────────────────────────
    cierres_qs = CierreCaja.objects.select_related('usuario', 'sucursal').order_by('-fecha', '-id')
    if sucursal:
        cierres_qs = cierres_qs.filter(sucursal=sucursal)
    ultimos_cierres = cierres_qs[:5]

    return {
        'total_semana':    f'{total_semana:,.2f}',
        'variacion':       variacion_txt,
        'ticket_promedio': f'{ticket_prom:,.2f}',
        'num_ventas':      num_ventas,
        'progreso_meta':   progreso,
        'objetivo':        f'{objetivo:,.0f}',
        'ventas_por_dia':  ventas_por_dia,
        'labels_dias':     labels_dias,
        'discrepancias':   discrepancias,
        'ultimos_cierres': ultimos_cierres,
        'sucursal_actual': sucursal,
        'fecha_rango':     f'{inicio_sem.strftime("%d %b")} - {ahora.strftime("%d %b, %Y")}',
        'usuario_nombre':  request.user.get_full_name() or request.user.username,
    }


@login_required(login_url='/')
@gerente_o_superior
def reportes_view(request):
    context = _get_contexto_reporte(request)
    return render(request, 'Reportes/Reportes.html', context)


@login_required(login_url='/')
@gerente_o_superior
def exportar_reporte_pdf(request):
    """Exporta el reporte semanal a PDF."""
    context  = _get_contexto_reporte(request)
    template = get_template('Reportes/Reportes_pdf.html')
    html     = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_semanal.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


@login_required(login_url='/')
@gerente_o_superior
def exportar_reporte_csv(request):
    """Exporta el reporte semanal a CSV."""
    context  = _get_contexto_reporte(request)
    sucursal = get_sucursal_contexto(request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reporte_semanal.csv"'
    
    # BOM para que Excel reconozca UTF-8 (acentos y ñ)
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Reporte Semanal — Llama y Carbón'])
    writer.writerow([f'Sucursal: {sucursal.nombre if sucursal else "Todas"}'])
    writer.writerow([f'Período: {context["fecha_rango"]}'])
    writer.writerow([])
    writer.writerow(['KPI', 'Valor'])
    writer.writerow(['Ventas Totales', f'${context["total_semana"]}'])
    writer.writerow(['Ticket Promedio', f'${context["ticket_promedio"]}'])
    writer.writerow(['Número de Ventas', context['num_ventas']])
    writer.writerow(['Progreso de Meta', f'{context["progreso_meta"]}%'])
    writer.writerow([])
    writer.writerow(['Día', 'Ventas ($)'])
    
    for dia, venta in zip(context['labels_dias'], context['ventas_por_dia']):
        writer.writerow([dia, f'${venta:.2f}'])

    return response