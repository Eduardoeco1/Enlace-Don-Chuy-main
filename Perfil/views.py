from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from EntradaMercancia.models import EntradaInsumo
from CierreCaja.models import CierreCaja


@login_required(login_url='/')
def perfil_view(request):
    usuario = request.user

    try:
        empleado = usuario.empleado
    except AttributeError:
        empleado = None

    entradas = EntradaInsumo.objects.order_by('-creado_en')[:2]
    cierres = CierreCaja.objects.filter(usuario=usuario).order_by('-fecha')[:2]

    actividad = []

    for e in entradas:
        actividad.append({
            'icono': 'inventory',
            'color': 'bg-secondary-fixed text-secondary',
            'accion': 'Entrada de Mercancía',
            'detalle': f'{e.producto} — {e.cantidad} {e.unidad}',
            'fecha': e.creado_en.strftime('%d %b, %H:%M'),
        })

    for c in cierres:
        actividad.append({
            'icono': 'point_of_sale',
            'color': 'bg-surface-container text-primary',
            'accion': 'Cierre de Caja',
            'detalle': f'Turno {c.get_turno_display()} — Diferencia: ${c.diferencia}',
            'fecha': f'{c.fecha.strftime("%d %b")}, {c.hora_cierre.strftime("%H:%M")}',
        })

    actividad.sort(key=lambda x: x['fecha'], reverse=True)

    context = {
        'usuario': usuario,
        'empleado': empleado,
        'nombre_completo': usuario.get_full_name() or usuario.username,
        'email': usuario.email or '—',
        'fecha_ingreso': usuario.date_joined.strftime('%d de %B, %Y'),
        'ultimo_login': usuario.last_login.strftime('%d %b, %H:%M') if usuario.last_login else '—',
        'actividad': actividad,
        'usuario_nombre': usuario.get_full_name() or usuario.username,
    }

    return render(request, 'Perfil/perfil.html', context)


@login_required(login_url='/')
def editar_perfil(request):
    usuario = request.user

    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name', '').strip()
        usuario.last_name = request.POST.get('last_name', '').strip()
        usuario.email = request.POST.get('email', '').strip()

        if request.FILES.get('foto_perfil'):
            if usuario.foto_perfil:
                usuario.foto_perfil.delete(save=False)

            usuario.foto_perfil = request.FILES['foto_perfil']

        password_actual = request.POST.get('password_actual', '').strip()
        password_nueva = request.POST.get('password_nueva', '').strip()
        password_confirmar = request.POST.get('password_confirmar', '').strip()

        quiere_cambiar_password = password_actual or password_nueva or password_confirmar

        if quiere_cambiar_password:
            if not password_actual:
                messages.error(request, '❌ Ingresa tu contraseña actual.')
                return redirect('Perfil:editar_perfil')

            if not usuario.check_password(password_actual):
                messages.error(request, '❌ La contraseña actual es incorrecta.')
                return redirect('Perfil:editar_perfil')

            if not password_nueva:
                messages.error(request, '❌ Ingresa una nueva contraseña.')
                return redirect('Perfil:editar_perfil')

            if len(password_nueva) < 8:
                messages.error(request, '❌ La nueva contraseña debe tener al menos 8 caracteres.')
                return redirect('Perfil:editar_perfil')

            if password_nueva != password_confirmar:
                messages.error(request, '❌ Las contraseñas nuevas no coinciden.')
                return redirect('Perfil:editar_perfil')

            usuario.set_password(password_nueva)

        usuario.save()

        if quiere_cambiar_password:
            update_session_auth_hash(request, usuario)
            messages.success(request, '✅ Perfil y contraseña actualizados correctamente.')
        else:
            messages.success(request, '✅ Perfil actualizado correctamente.')

        return redirect('Perfil:perfil')

    context = {
        'usuario': usuario,
        'usuario_nombre': usuario.get_full_name() or usuario.username,
    }

    return render(request, 'Perfil/editar_perfil.html', context)



