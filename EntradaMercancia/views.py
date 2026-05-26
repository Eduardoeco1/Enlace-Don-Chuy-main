from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import EntradaInsumo
from .forms import EntradaInsumoForm
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


def _es_duena(user):
    return (
        user.is_superuser or
        (hasattr(user, 'rol') and user.rol in ['duena', 'dueña']) or
        user.groups.filter(name='Dueña').exists()
    )


def _obtener_sucursal_usuario(request):
    sucursal = get_sucursal_contexto(request)
    es_duena = _es_duena(request.user)

    if not es_duena:
        if hasattr(request.user, 'empleado') and request.user.empleado.sucursal:
            sucursal = request.user.empleado.sucursal
        elif hasattr(request.user, 'sucursal') and request.user.sucursal:
            sucursal = request.user.sucursal

    return sucursal, es_duena


@login_required(login_url='/')
@cualquier_rol
def entrada_mercancia_view(request):
    sucursal_actual, es_duena = _obtener_sucursal_usuario(request)

    if request.method == 'POST':
        form = EntradaInsumoForm(
            request.POST,
            user=request.user,
            sucursal_actual=sucursal_actual
        )

        if form.is_valid():
            entrada = form.save(commit=False)

            if not es_duena:
                entrada.sucursal = sucursal_actual

            if not entrada.sucursal:
                messages.error(request, '❌ Debes tener una sucursal asignada.')
                return redirect('EntradaMercancia:entrada')

            entrada.save()

            messages.success(
                request,
                f'✅ Entrada registrada: {entrada.producto} ({entrada.cantidad} {entrada.unidad}).'
            )
            return redirect('EntradaMercancia:entrada')

        messages.error(request, '❌ Corrige los errores en el formulario.')

    else:
        form = EntradaInsumoForm(
            user=request.user,
            sucursal_actual=sucursal_actual
        )

    entradas = EntradaInsumo.objects.select_related('sucursal').all()

    if sucursal_actual:
        entradas = entradas.filter(sucursal=sucursal_actual)
    elif not es_duena:
        entradas = entradas.none()

    entradas = entradas.order_by('-creado_en')[:20]

    context = {
        'form': form,
        'entradas': entradas,
        'sucursal_actual': sucursal_actual,
        'es_duena': es_duena,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'EntradaMercancia/enmer.html', context)



