from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from EntradaMercancia.models import EntradaInsumo
from CierreCaja.models import CierreCaja

@login_required(login_url='/')
def perfil_view(request):
    usuario = request.user

    # Actividad reciente combinando modelos existentes
    entradas  = EntradaInsumo.objects.order_by('-creado_en')[:2]
    cierres   = CierreCaja.objects.filter(usuario=usuario).order_by('-fecha')[:2]

    actividad = []
    for e in entradas:
        actividad.append({
            'icono':      'inventory',
            'color':      'bg-secondary-fixed text-secondary',
            'accion':     'Entrada de Mercancía',
            'detalle':    f'{e.producto} — {e.cantidad} {e.unidad}',
            'fecha':      e.creado_en.strftime('%d %b, %H:%M'),
        })
    for c in cierres:
        actividad.append({
            'icono':      'point_of_sale',
            'color':      'bg-surface-container text-primary',
            'accion':     'Cierre de Caja',
            'detalle':    f'Turno {c.get_turno_display()} — Diferencia: ${c.diferencia}',
            'fecha':      f'{c.fecha.strftime("%d %b")}, {c.hora_cierre.strftime("%H:%M")}',
        })

    actividad.sort(key=lambda x: x['fecha'], reverse=True)

    context = {
        'usuario':         usuario,
        'nombre_completo': usuario.get_full_name() or usuario.username,
        'email':           usuario.email or '—',
        'fecha_ingreso':   usuario.date_joined.strftime('%d de %B, %Y'),
        'ultimo_login':    usuario.last_login.strftime('%d %b, %H:%M') if usuario.last_login else '—',
        'actividad':       actividad,
        'usuario_nombre':  usuario.get_full_name() or usuario.username,
    }
    return render(request, 'Perfil/perfil.html', context)

