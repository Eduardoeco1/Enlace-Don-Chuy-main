from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Sucursal
from .permisos import solo_duena


@login_required(login_url='/')
@solo_duena
def cambiar_sucursal(request):
    """
    La Dueña selecciona una sucursal para ver sus datos mediante formulario clásico.
    POST: { sucursal_id }  — poner '' para ver todas.
    """
    sid = request.POST.get('sucursal_id', '')
    next_url = request.POST.get('next', '/panel-control/')

    if sid == '' or sid is None or sid == 'todas':
        # Ver todas las sucursales
        request.session.pop('sucursal_activa_id', None)
        request.session.pop('sucursal_global_id', None)
        messages.success(request, '👁️ Viendo datos de todas las sucursales.')
    else:
        try:
            suc = Sucursal.objects.get(id=sid, activa=True)
            request.session['sucursal_activa_id'] = suc.id
            request.session['sucursal_global_id'] = suc.id
            messages.success(request, f'📍 Contexto cambiado a {suc.nombre}.')
        except Sucursal.DoesNotExist:
            messages.error(request, 'Sucursal no encontrada.')

    return redirect(next_url)


@login_required(login_url='/')
@require_POST
def cambiar_sucursal_global(request):
    """
    Cambiar la sucursal global en la sesión mediante una petición AJAX (JSON).
    Solo para Dueña o Superusuarios.
    """
    if not (request.user.is_superuser or getattr(request.user, 'rol', None) == 'duena' or request.user.groups.filter(name='Dueña').exists()):
        return JsonResponse({'ok': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        data = json.loads(request.body)
        sucursal_id = data.get('sucursal_id')
        
        if sucursal_id and sucursal_id != 'todas' and str(sucursal_id).strip() != '':
            sid_int = int(sucursal_id)
            if Sucursal.objects.filter(id=sid_int, activa=True).exists():
                request.session['sucursal_global_id'] = sid_int
                request.session['sucursal_activa_id'] = sid_int
            else:
                return JsonResponse({'ok': False, 'error': 'La sucursal no existe o está inactiva'}, status=404)
        else:
            request.session['sucursal_global_id'] = None
            request.session['sucursal_activa_id'] = None
        
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    


    