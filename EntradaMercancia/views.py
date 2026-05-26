from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import EntradaInsumo
from .forms import EntradaInsumoForm
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


@login_required(login_url='/')
@cualquier_rol
def entrada_mercancia_view(request):
    sucursal_actual = get_sucursal_contexto(request)

    es_duena = (
        request.user.is_superuser or
        (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']) or
        request.user.groups.filter(name='Dueña').exists()
    )

    if request.method == 'POST':
        form = EntradaInsumoForm(
            request.POST,
            user=request.user,
            sucursal_actual=sucursal_actual
        )

        if form.is_valid():
            entrada = form.save(commit=False)

            if not es_duena and sucursal_actual:
                entrada.sucursal = sucursal_actual

            if not entrada.sucursal:
                messages.error(request, '❌ Debes seleccionar una sucursal.')
                return redirect('EntradaMercancia:entrada')

            entrada.save()

            messages.success(
                request,
                f'✅ Entrada registrada: {entrada.producto} ({entrada.cantidad} {entrada.unidad}). '
                f'El inventario se actualizará automáticamente.'
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

    entradas = entradas.order_by('-creado_en')[:20]

    context = {
        'form': form,
        'entradas': entradas,
        'sucursal_actual': sucursal_actual,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }

    return render(request, 'EntradaMercancia/enmer.html', context)