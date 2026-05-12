from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth import get_user_model

# Modelos y Formularios locales
from .models import Empleado, Turno, Asistencia
from .forms import (
    EmpleadoForm, MarcarEntradaForm, MarcarSalidaForm, 
    JustificanteForm, AsistenciaAdminForm
)

# Permisos y modelos externos
from Sucursales.permisos import gerente_o_superior, cualquier_rol, get_sucursal_contexto
from Sucursales.models import Sucursal

User = get_user_model()

@login_required(login_url='/')
@gerente_o_superior
def personal_view(request):
    sucursal    = get_sucursal_contexto(request)
    busqueda    = request.GET.get('q', '')
    sucursal_id = request.GET.get('sucursal', '')
    rol_sel     = request.GET.get('rol', '')

    form = EmpleadoForm()
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
            nuevo_user = User.objects.create_user(
                username   = d['username'],
                email      = d['email'],
                password   = d['password'],
                first_name = d['first_name'],
                last_name  = d['last_name'],
            )
            
            Empleado.objects.create(
                usuario  = nuevo_user,
                rol      = d['rol'], 
                sucursal = d['sucursal'],
                estado   = d.get('estado', 'offline'),
                telefono = d.get('telefono', ''),
            )
            
            messages.success(request, f'✅ Usuario "{nuevo_user.username}" registrado correctamente.')
            return redirect('Personal:personal')
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')

    empleados = Empleado.objects.select_related('usuario', 'sucursal').all()

    if sucursal:
        empleados = empleados.filter(sucursal=sucursal)
    elif sucursal_id and request.user.is_superuser:
        empleados = empleados.filter(sucursal__id=sucursal_id)

    if rol_sel:
        empleados = empleados.filter(rol=rol_sel)

    if busqueda:
        empleados = (
            empleados.filter(usuario__username__icontains=busqueda) |
            empleados.filter(usuario__first_name__icontains=busqueda) |
            empleados.filter(usuario__last_name__icontains=busqueda)  |
            empleados.filter(usuario__email__icontains=busqueda)
        )

    page_obj = Paginator(empleados, 10).get_page(request.GET.get('page', 1))

    base_qs = Empleado.objects.all()
    if sucursal:
        base_qs = base_qs.filter(sucursal=sucursal)

    total_empleados = base_qs.count()
    activos         = base_qs.filter(estado='activo').count()
    en_turno        = base_qs.filter(en_turno=True).count()

    roles_cobertura = []
    for cod_rol, nombre_rol in Empleado.ROLES_CHOICES:
        qs_rol    = base_qs.filter(rol=cod_rol)
        activos_r = qs_rol.filter(estado='activo').count()
        minimo = 1 if cod_rol == 'gerente' else 3 
        pct    = min(int((activos_r / minimo * 100)), 100) if minimo > 0 else 100
        
        roles_cobertura.append({
            'nombre': nombre_rol, 'activos': activos_r, 'minimo': minimo,
            'porcentaje': pct, 'critico': pct < 50, 'bajo': 50 <= pct < 100,
        })

    turnos_qs = Turno.objects.filter(fecha__gte=timezone.now().date()).select_related('sucursal').order_by('fecha', 'hora_inicio')
    
    if sucursal:
        turnos_qs = turnos_qs.filter(sucursal=sucursal)

    context = {
        'page_obj': page_obj, 'total_empleados': total_empleados, 'activos': activos,
        'en_turno': en_turno, 'roles_cobertura': roles_cobertura, 'proximos_turnos': turnos_qs[:3],
        'sucursales': Sucursal.objects.all(), 'roles_list': Empleado.ROLES_CHOICES,
        'form': form, 'busqueda': busqueda, 'sucursal_sel': sucursal_id,
        'rol_sel': rol_sel, 'sucursal_actual': sucursal,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/personal.html', context)


@login_required(login_url='/')
@gerente_o_superior
def editar_empleado_view(request, empleado_id):
    """Actualiza datos, rol o sucursal del personal."""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario
    
    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name  = request.POST.get('last_name')
        usuario.email      = request.POST.get('email')
        usuario.username   = request.POST.get('username')
        
        password = request.POST.get('password')
        if password and password.strip():
            usuario.set_password(password)
        usuario.save()
        
        empleado.rol       = request.POST.get('rol')
        empleado.sucursal_id = request.POST.get('sucursal')
        empleado.estado    = request.POST.get('estado')
        empleado.telefono  = request.POST.get('telefono')
        empleado.save()
        
        messages.success(request, f'✅ Datos de "{usuario.username}" actualizados.')
    return redirect('Personal:personal')


@login_required(login_url='/')
@gerente_o_superior
def eliminar_empleado_view(request, empleado_id):
    """Elimina permanentemente al empleado y su cuenta de acceso."""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario

    if usuario == request.user:
        messages.error(request, "❌ No puedes eliminar tu propia cuenta administrativa.")
        return redirect('Personal:personal')

    username_borrado = usuario.username
    usuario.delete() 
    
    messages.success(request, f'✅ El empleado "{username_borrado}" ha sido eliminado.')
    return redirect('Personal:personal')


@login_required(login_url='/')
@cualquier_rol
def marcar_asistencia(request):
    """El empleado marca su entrada o salida."""
    try:
        empleado = request.user.empleado
    except Exception:
        messages.error(request, '❌ Tu usuario no tiene perfil de empleado.')
        return redirect('PanelControl:panel')

    hoy = timezone.now().date()
    asistencia, _ = Asistencia.objects.get_or_create(
        empleado = empleado,
        fecha    = hoy,
        defaults = {'estado': 'presente'},
    )

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'entrada':
            form = MarcarEntradaForm(request.POST)
            if form.is_valid():
                asistencia.hora_entrada   = form.cleaned_data['hora_entrada']
                asistencia.estado         = 'presente'
                asistencia.registrado_por = request.user
                asistencia.save()
                messages.success(request, f'✅ Entrada registrada a las {asistencia.hora_entrada}')

        elif accion == 'salida':
            form = MarcarSalidaForm(request.POST)
            if form.is_valid():
                asistencia.hora_salida    = form.cleaned_data['hora_salida']
                asistencia.registrado_por = request.user
                asistencia.save()
                messages.success(
                    request,
                    f'✅ Salida registrada. Total trabajado: {asistencia.horas_trabajadas} hrs'
                )

        elif accion == 'justificante':
            form_just = JustificanteForm(request.POST, request.FILES, instance=asistencia)
            if form_just.is_valid():
                inst         = form_just.save(commit=False)
                inst.estado  = 'ausente'
                inst.save()
                messages.success(request, '✅ Justificante subido correctamente.')

        return redirect('Personal:asistencia')

    context = {
        'asistencia':    asistencia,
        'form_entrada':  MarcarEntradaForm(initial={'hora_entrada': timezone.now().strftime('%H:%M')}),
        'form_salida':   MarcarSalidaForm(initial={'hora_salida':  timezone.now().strftime('%H:%M')}),
        'form_just':     JustificanteForm(instance=asistencia),
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/asistencia_empleado.html', context)


@login_required(login_url='/')
@gerente_o_superior
def tabla_asistencias(request):
    """Vista de administrador con tabla completa de asistencias."""
    sucursal = get_sucursal_contexto(request)

    fecha_str   = request.GET.get('fecha', timezone.now().date().isoformat())
    empleado_id = request.GET.get('empleado', '')

    try:
        fecha_filtro = timezone.datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_filtro = timezone.now().date()

    asistencias = Asistencia.objects.select_related(
        'empleado__usuario', 'empleado__sucursal'
    ).filter(fecha=fecha_filtro)

    if sucursal:
        asistencias = asistencias.filter(empleado__sucursal=sucursal)
    if empleado_id:
        asistencias = asistencias.filter(empleado__id=empleado_id)

    form_admin = AsistenciaAdminForm()
    if request.method == 'POST':
        form_admin = AsistenciaAdminForm(request.POST, request.FILES)
        if form_admin.is_valid():
            inst = form_admin.save(commit=False)
            inst.registrado_por = request.user
            inst.save()
            messages.success(request, '✅ Asistencia registrada correctamente.')
            return redirect('Personal:asistencias')
        else:
            messages.error(request, '❌ Corrige los errores en el formulario.')

    # Estadísticas del día
    presentes   = asistencias.filter(estado='presente').count()
    ausentes    = asistencias.filter(estado='ausente').count()
    descansos   = asistencias.filter(es_dia_descanso=True).count()

    empleados_qs = Empleado.objects.select_related('usuario')
    if sucursal:
        empleados_qs = empleados_qs.filter(sucursal=sucursal)

    context = {
        'asistencias':   asistencias,
        'fecha_filtro':  fecha_filtro,
        'empleado_id':   empleado_id,
        'form_admin':    form_admin,
        'total':         asistencias.count(),
        'presentes':     presentes,
        'ausentes':      ausentes,
        'descansos':     descansos,
        'empleados':     empleados_qs,
        'sucursal_actual': sucursal,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/asistencias_admin.html', context)




