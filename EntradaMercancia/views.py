from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import EntradaInsumo
from .forms import EntradaInsumoForm
from Sucursales.permisos import cualquier_rol, get_sucursal_contexto


@login_required(login_url='/')
@cualquier_rol
def entrada_mercancia_view(request):
    sucursal = get_sucursal_contexto(request)

    if request.method == 'POST':
        form = EntradaInsumoForm(request.POST)
        if form.is_valid():
            entrada = form.save(commit=False)
            # Asigna sucursal del usuario automáticamente
            if sucursal:
                entrada.sucursal = sucursal
            entrada.save()
            messages.success(request, '✅ Entrada registrada correctamente.')
            return redirect('EntradaMercancia:entrada')
        else:
            messages.error(request, '⚠️ Corrige los errores en el formulario.')
    else:
        form = EntradaInsumoForm()

    # ── Últimas entradas filtradas por sucursal ───────
    ultimas = EntradaInsumo.objects.all()
    if sucursal:
        ultimas = ultimas.filter(sucursal=sucursal)
    ultimas = ultimas[:5]

    context = {
        'form':            form,
        'ultimas_entradas': ultimas,
        'fecha_actual':    timezone.now().strftime('%d de %B, %Y'),
        'sucursal_actual': sucursal,
        'usuario_nombre':  request.user.get_full_name() or request.user.username,
    }
    return render(request, 'EntradaMercancia/enmer.html', context)


