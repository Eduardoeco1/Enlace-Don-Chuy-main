import csv
from decimal import Decimal
from datetime import date, datetime, timedelta

from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, F, Count
from django.template.loader import get_template
from django.utils import timezone

from xhtml2pdf import pisa

from Ventas.models import Pedido, DetallePedido
from CierreCaja.models import CierreCaja
from Reportes.models import Insumo, MetaSemanal
from Sucursales.models import Sucursal
from Sucursales.permisos import gerente_o_superior


ESTADOS_VALIDOS_VENTAS = ['procesado', 'procesada', 'COMPLETADA', 'completado']


def _es_duena(user):
    return (
        user.is_superuser
        or (hasattr(user, 'rol') and user.rol in ['duena', 'dueña'])
        or user.groups.filter(name='Dueña').exists()
    )


def _obtener_fechas_y_sucursal(request):
    periodo = request.GET.get('periodo', 'hoy')
    hoy = timezone.now().date()

    if periodo == 'hoy':
        fecha_inicio, fecha_fin = hoy, hoy
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = hoy
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy
    elif periodo == 'personalizado':
        try:
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            fecha_inicio, fecha_fin = hoy, hoy
    else:
        fecha_inicio, fecha_fin = hoy, hoy

    sucursal_usuario = getattr(request, 'sucursal_actual', None)
    sucursal_id_get = request.GET.get('sucursal_id')

    if sucursal_id_get and sucursal_id_get != 'todas':
        try:
            sucursal_id = int(sucursal_id_get)
        except ValueError:
            sucursal_id = sucursal_usuario.id if sucursal_usuario else None
    elif sucursal_id_get == 'todas' and _es_duena(request.user):
        sucursal_id = None
    elif sucursal_usuario:
        sucursal_id = sucursal_usuario.id
    else:
        sucursal_id = None

    return fecha_inicio, fecha_fin, sucursal_id


def _get_contexto_reporte(request):
    fecha_inicio, fecha_fin, sucursal_id = _obtener_fechas_y_sucursal(request)

    es_duena = _es_duena(request.user)

    sucursal_activa = None
    if sucursal_id:
        sucursal_activa = Sucursal.objects.filter(id=sucursal_id).first()

    dias_del_periodo = (fecha_fin - fecha_inicio).days + 1
    fecha_inicio_ant = fecha_inicio - timedelta(days=dias_del_periodo)
    fecha_fin_ant = fecha_inicio - timedelta(days=1)

    pedidos_qs = Pedido.objects.filter(estado__in=ESTADOS_VALIDOS_VENTAS)
    meta_qs = MetaSemanal.objects.all()
    disc_qs = Insumo.objects.filter(stock_fisico__lt=F('stock_esperado'))
    cierres_qs = CierreCaja.objects.select_related('usuario', 'sucursal')

    if sucursal_activa:
        pedidos_qs = pedidos_qs.filter(sucursal=sucursal_activa)
        meta_qs = meta_qs.filter(sucursal=sucursal_activa)
        disc_qs = disc_qs.filter(sucursal=sucursal_activa)
        cierres_qs = cierres_qs.filter(sucursal=sucursal_activa)
    elif not es_duena:
        pedidos_qs = pedidos_qs.none()
        meta_qs = meta_qs.none()
        disc_qs = disc_qs.none()
        cierres_qs = cierres_qs.none()

    ventas_actuales = pedidos_qs.filter(
        creado_en__date__gte=fecha_inicio,
        creado_en__date__lte=fecha_fin
    )

    ventas_anteriores = pedidos_qs.filter(
        creado_en__date__gte=fecha_inicio_ant,
        creado_en__date__lte=fecha_fin_ant
    )

    total_semana = ventas_actuales.aggregate(t=Sum('total'))['t'] or Decimal('0')
    total_sem_ant = ventas_anteriores.aggregate(t=Sum('total'))['t'] or Decimal('0')
    ticket_prom = ventas_actuales.aggregate(a=Avg('total'))['a'] or Decimal('0')
    num_ventas = ventas_actuales.count()

    if total_sem_ant > 0:
        variacion = ((total_semana - total_sem_ant) / total_sem_ant) * 100
        variacion_txt = f'+{variacion:.1f}% vs ant.' if variacion >= 0 else f'{variacion:.1f}% vs ant.'
    else:
        variacion_txt = 'Sin datos anteriores'

    meta = meta_qs.order_by('-fecha_inicio').first()
    objetivo = meta.objetivo_monto if meta else Decimal('175000')
    progreso = min(int((total_semana / objetivo) * 100), 100) if objetivo > 0 else 0

    ventas_por_dia = []
    labels_dias = []
    dias_semana = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']

    if fecha_inicio == fecha_fin:
        for hora in range(9, 23, 2):
            qs_h = pedidos_qs.filter(
                creado_en__date=fecha_inicio,
                creado_en__hour=hora
            )
            total_h = qs_h.aggregate(t=Sum('total'))['t'] or 0
            ventas_por_dia.append(float(total_h))
            labels_dias.append(f'{hora}:00')
    else:
        pasos = min(dias_del_periodo, 7)

        for i in range(pasos - 1, -1, -1):
            dia = fecha_fin - timedelta(days=i)
            qs_d = pedidos_qs.filter(creado_en__date=dia)
            total_d = qs_d.aggregate(t=Sum('total'))['t'] or 0
            ventas_por_dia.append(float(total_d))
            labels_dias.append(dias_semana[dia.weekday()])

    discrepancias = disc_qs.order_by('stock_fisico')[:10]

    ultimos_cierres = cierres_qs.filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by('-fecha', '-id')[:5]

    return {
        'total_semana': f'{total_semana:,.2f}',
        'variacion': variacion_txt,
        'ticket_promedio': f'{ticket_prom:,.2f}',
        'num_ventas': num_ventas,
        'progreso_meta': progreso,
        'objetivo': f'{objetivo:,.0f}',
        'ventas_por_dia': ventas_por_dia,
        'labels_dias': labels_dias,
        'discrepancias': discrepancias,
        'ultimos_cierres': ultimos_cierres,
        'sucursal_actual': sucursal_activa,
        'es_duena': es_duena,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_rango': f'{fecha_inicio.strftime("%d %b")} - {fecha_fin.strftime("%d %b, %Y")}',
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }


@login_required(login_url='/')
@gerente_o_superior
def reporte_view(request):
    reporte_context = _get_contexto_reporte(request)
    sucursal = reporte_context['sucursal_actual']

    fecha_inicio = reporte_context['fecha_inicio']
    fecha_fin = reporte_context['fecha_fin']
    periodo = request.GET.get('periodo', 'hoy')

    pedidos = Pedido.objects.filter(
        creado_en__date__gte=fecha_inicio,
        creado_en__date__lte=fecha_fin,
        estado__in=ESTADOS_VALIDOS_VENTAS
    )

    if sucursal:
        pedidos = pedidos.filter(sucursal=sucursal)
    elif not reporte_context['es_duena']:
        pedidos = pedidos.none()

    stats = pedidos.aggregate(
        total_ventas=Sum('total'),
        total_pedidos=Count('id')
    )

    context = {
        'pedidos': pedidos.order_by('-creado_en')[:50],
        'total_ventas': stats['total_ventas'] or 0,
        'total_pedidos': stats['total_pedidos'] or 0,

        'periodo': periodo,
        'periodo_actual': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,

        'sucursales': Sucursal.objects.all(),
        'sucursal_id_actual': request.GET.get('sucursal_id', str(sucursal.id) if sucursal else 'todas'),

        'total_semana': reporte_context['total_semana'],
        'variacion': reporte_context['variacion'],
        'ticket_promedio': reporte_context['ticket_promedio'],
        'num_ventas': reporte_context['num_ventas'],
        'progreso_meta': reporte_context['progreso_meta'],
        'objetivo': reporte_context['objetivo'],
        'ventas_por_dia': reporte_context['ventas_por_dia'],
        'labels_dias': reporte_context['labels_dias'],
        'discrepancias': reporte_context['discrepancias'],
        'ultimos_cierres': reporte_context['ultimos_cierres'],
        'sucursal_actual': reporte_context['sucursal_actual'],
        'es_duena': reporte_context['es_duena'],
        'fecha_rango': reporte_context['fecha_rango'],
        'usuario_nombre': reporte_context['usuario_nombre'],
    }

    return render(request, 'Reportes/Reportes.html', context)


@login_required(login_url='/')
@gerente_o_superior
def exportar_reporte_pdf(request):
    context = _get_contexto_reporte(request)
    template = get_template('Reportes/Reportes_pdf.html')
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_desempeno.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response


@login_required(login_url='/')
@gerente_o_superior
def exportar_reporte_csv(request):
    context = _get_contexto_reporte(request)
    sucursal = context['sucursal_actual']

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reporte_desempeno.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Reporte de Desempeño — Enlace Don Chuy'])
    writer.writerow([f'Sucursal: {sucursal.nombre if sucursal else "Todas las Sucursales"}'])
    writer.writerow([f'Período Evaluado: {context["fecha_rango"]}'])
    writer.writerow([])

    writer.writerow(['Indicador KPI', 'Valor Evaluado'])
    writer.writerow(['Ventas Totales', f'${context["total_semana"]}'])
    writer.writerow(['Ticket Promedio', f'${context["ticket_promedio"]}'])
    writer.writerow(['Volumen de Ventas', context['num_ventas']])
    writer.writerow(['Progreso Cumplimiento Meta', f'{context["progreso_meta"]}%'])
    writer.writerow([])

    writer.writerow(['Intervalo Temporal', 'Ingreso Registrado ($)'])

    for dia, venta in zip(context['labels_dias'], context['ventas_por_dia']):
        writer.writerow([dia, f'${venta:.2f}'])

    return response


@login_required(login_url='/')
@gerente_o_superior
def exportar_consolidado_csv(request):
    if not _es_duena(request.user):
        messages.error(request, '❌ No tienes permisos para exportar el consolidado global de auditoría.')
        return redirect('/reportes/')

    fecha_inicio, fecha_fin, _ = _obtener_fechas_y_sucursal(request)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="reporte_consolidado_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Ticket', 'Sucursal', 'Producto', 'Cantidad', 'Precio Unit.', 'Total'])

    detalles = DetallePedido.objects.filter(
        pedido__creado_en__date__gte=fecha_inicio,
        pedido__creado_en__date__lte=fecha_fin,
        pedido__estado__in=ESTADOS_VALIDOS_VENTAS
    ).select_related(
        'pedido',
        'pedido__sucursal',
        'producto'
    ).order_by('pedido__sucursal__nombre', '-pedido__creado_en')

    for detalle in detalles:
        cant = detalle.amount if hasattr(detalle, 'amount') else detalle.cantidad

        writer.writerow([
            detalle.pedido.creado_en.strftime('%Y-%m-%d'),
            detalle.pedido.id,
            detalle.pedido.sucursal.nombre if detalle.pedido.sucursal else 'N/A',
            detalle.producto.nombre,
            cant,
            float(detalle.precio_u),
            float(cant * detalle.precio_u),
        ])

    return response


@login_required(login_url='/')
@gerente_o_superior
def exportar_sucursal_csv(request):
    fecha_inicio, fecha_fin, sucursal_id = _obtener_fechas_y_sucursal(request)

    if not sucursal_id:
        messages.warning(
            request,
            '⚠️ Para exportar transacciones detalladas por sucursal, primero selecciona una tienda específica.'
        )
        return redirect('Reportes:reporte')

    try:
        sucursal = Sucursal.objects.get(id=int(sucursal_id))
    except Sucursal.DoesNotExist:
        messages.error(request, '❌ La sucursal solicitada no existe.')
        return redirect('Reportes:reporte')

    detalles = DetallePedido.objects.filter(
        pedido__creado_en__date__gte=fecha_inicio,
        pedido__creado_en__date__lte=fecha_fin,
        pedido__estado__in=ESTADOS_VALIDOS_VENTAS,
        pedido__sucursal=sucursal
    ).select_related('pedido', 'producto').order_by('-pedido__creado_en')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="reporte_{sucursal.nombre.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Ticket', 'Producto', 'Cantidad', 'Precio Unit.', 'Total'])

    for detalle in detalles:
        cant = detalle.amount if hasattr(detalle, 'amount') else detalle.cantidad

        writer.writerow([
            detalle.pedido.creado_en.strftime('%Y-%m-%d'),
            detalle.pedido.id,
            detalle.producto.nombre,
            cant,
            float(detalle.precio_u),
            float(cant * detalle.precio_u),
        ])

    return response

@login_required(login_url='/')
@gerente_o_superior
def actualizar_meta_semanal(request):
    if request.method != 'POST':
        return redirect('Reportes:reporte')

    if not _es_duena(request.user):
        messages.error(request, '❌ Solo la dueña puede modificar la meta semanal.')
        return redirect('Reportes:reporte')

    sucursal_id = request.POST.get('sucursal_id')
    objetivo = request.POST.get('objetivo_monto')

    if not objetivo:
        messages.error(request, '❌ Ingresa un monto válido para la meta.')
        return redirect('Reportes:reporte')

    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    sucursal = None
    if sucursal_id and sucursal_id != 'todas':
        sucursal = Sucursal.objects.filter(id=sucursal_id).first()

    meta, creada = MetaSemanal.objects.update_or_create(
        sucursal=sucursal,
        fecha_inicio=inicio_semana,
        defaults={
            'objetivo_monto': objetivo,
        }
    )

    messages.success(request, '✅ Meta semanal actualizada correctamente.')
    return redirect('Reportes:reporte')





