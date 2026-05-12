from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sucursal
from .permisos import solo_duena


@login_required(login_url='/')
@solo_duena
def cambiar_sucursal(request):
    """
    La Dueña selecciona una sucursal para ver sus datos.
    POST: { sucursal_id }  — poner '' para ver todas.
    """
    sid = request.POST.get('sucursal_id', '')
    next_url = request.POST.get('next', '/panel-control/')

    if sid == '' or sid is None:
        # Ver todas las sucursales
        request.session.pop('sucursal_activa_id', None)
        messages.success(request, '👁️ Viendo datos de todas las sucursales.')
    else:
        try:
            suc = Sucursal.objects.get(id=sid, activa=True)
            request.session['sucursal_activa_id'] = suc.id
            messages.success(request, f'📍 Contexto cambiado a {suc.nombre}.')
        except Sucursal.DoesNotExist:
            messages.error(request, 'Sucursal no encontrada.')

    return redirect(next_url)

