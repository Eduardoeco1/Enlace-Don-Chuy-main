from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from datetime import datetime

# Importación del Sistema de Notificaciones Centralizado
from Notificaciones.models import Notificacion

# Modelos y Formularios locales
from .models import Empleado, Turno, Asistencia, Justificante
from .forms import (
    EmpleadoForm, MarcarEntradaForm, MarcarSalidaForm, 
    JustificanteForm, AsistenciaAdminForm, JustificanteCreateForm
)

# ── IMPORTAMOS LOS DECORADORES (Eliminamos get_sucursal_contexto) ──
from Sucursales.permisos import gerente_o_superior, cualquier_rol, solo_duena
from Sucursales.models import Sucursal

User = get_user_model()

# ==========================================
# VISTAS DE ADMINISTRACIÓN DE PERSONAL
# ==========================================

@login_required(login_url='/')
@gerente_o_superior
def personal_view(request):
    """
    Vista principal de administración de personal.
    Accesible para Gerentes y Dueña, filtrando automáticamente por sucursal activa.
    """
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal    = getattr(request, 'sucursal_actual', None)
    busqueda    = request.GET.get('q', '')
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
                sucursal = d['sucursal'] or sucursal,
                estado   = d.get('estado', 'offline'),
                telefono = d.get('telefono', ''),
            )
            messages.success(request, f'✅ Usuario "{nuevo_user.username}" registrado correctamente.')
            return redirect('Personal:personal')
        else:
            print(form.errors)
            messages.error(request, '❌ Corrige los errores en el formulario.')

    empleados = Empleado.objects.select_related('usuario', 'sucursal').all()
    # ── FILTRO DINÁMICO ──
    if sucursal:
        empleados = empleados.filter(sucursal=sucursal)

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
    # ── FILTRO DINÁMICO ──
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

    turnos_qs = Turno.objects.filter(fecha__gte=timezone.now().date()).select_related('empleado__usuario').order_by('fecha', 'hora_inicio')
    # ── FILTRO DINÁMICO ──
    if sucursal:
        turnos_qs = turnos_qs.filter(sucursal=sucursal)

    context = {
        'page_obj': page_obj, 'total_empleados': total_empleados, 'activos': activos,
        'en_turno': en_turno, 'roles_cobertura': roles_cobertura, 'proximos_turnos': turnos_qs[:5],
        'roles_list': Empleado.ROLES_CHOICES,
        'form': form, 'busqueda': busqueda,
        'rol_sel': rol_sel, 
        'base_qs': base_qs,
        # Ya no se pasan 'sucursales' ni 'sucursal_actual' porque context_processor las provee
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/personal.html', context)


@login_required(login_url='/')
@gerente_o_superior
def editar_empleado_view(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal_global = getattr(request, 'sucursal_actual', None)
    es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))
    
    if not es_duena and sucursal_global and empleado.sucursal != sucursal_global:
        messages.error(request, '🚫 No puedes editar empleados fuera de tu sucursal.')
        return redirect('Personal:personal')

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
    empleado = get_object_or_404(Empleado, id=empleado_id)
    usuario = empleado.usuario
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal_global = getattr(request, 'sucursal_actual', None)
    es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))

    if not es_duena and sucursal_global and empleado.sucursal != sucursal_global:
        messages.error(request, '🚫 No puedes eliminar empleados fuera de tu sucursal.')
        return redirect('Personal:personal')

    if usuario == request.user:
        messages.error(request, "❌ No puedes eliminar tu propia cuenta administrativa.")
        return redirect('Personal:personal')
    username_borrado = usuario.username
    usuario.delete() 
    messages.success(request, f'✅ El empleado "{username_borrado}" ha sido eliminado.')
    return redirect('Personal:personal')


# ==========================================
# VISTAS DE GESTIÓN DE TURNOS (COMPLETO)
# ==========================================

@login_required(login_url='/')
@gerente_o_superior
@require_POST
def guardar_turno(request):
    """
    Guarda o actualiza un turno operativo desde el modal AJAX.
    Sincronizado con la sucursal activa.
    """
    try:
        empleado_id = request.POST.get('empleado_id')
        fecha = parse_date(request.POST.get('fecha'))
        tipo_turno = request.POST.get('tipo_turno')
        notas = request.POST.get('notas', '')
        # ── MODIFICACIÓN: Leer directamente del Middleware ──
        sucursal = getattr(request, 'sucursal_actual', None)
        es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))
        
        if tipo_turno == 'matutino':
            hora_inicio = parse_time('08:00')
            hora_fin = parse_time('13:00')
        elif tipo_turno == 'vespertino':
            hora_inicio = parse_time('13:00')
            hora_fin = parse_time('20:00')
        else:  # medio_tiempo
            hora_inicio = parse_time(request.POST.get('hora_inicio'))
            hora_fin = parse_time(request.POST.get('hora_fin'))
        
        empleado = Empleado.objects.get(id=empleado_id)
        
        # Validación de aislamiento multisucursal
        if not es_duena and sucursal and empleado.sucursal != sucursal:
            messages.error(request, '🚫 No tienes permiso para asignar turnos a personal de otra sucursal.')
            return redirect('Personal:personal')
        
        turno, created = Turno.objects.update_or_create(
            empleado=empleado,
            fecha=fecha,
            defaults={
                'tipo_turno': tipo_turno,
                'hora_inicio': hora_inicio,
                'hora_fin': hora_fin,
                'notas': notas,
                'sucursal': sucursal or empleado.sucursal,
                'creado_por': request.user
            }
        )
        
        if created:
            messages.success(request, f'✅ Turno creado para {empleado.nombre_completo()}')
        else:
            messages.success(request, f'✅ Turno actualizado para {empleado.nombre_completo()}')
        
    except Exception as e:
        messages.error(request, f'❌ Error: {e}')
    
    return redirect('Personal:personal')


@login_required(login_url='/')
@gerente_o_superior
def programar_turno(request):
    """Vista completa para agendar turnos operativos."""
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal = getattr(request, 'sucursal_actual', None)
    es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))
    
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado_id')
        fecha = parse_date(request.POST.get('fecha'))
        tipo_turno = request.POST.get('tipo_turno')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        notes = request.POST.get('notas', '')
        
        try:
            empleado = Empleado.objects.get(id=empleado_id)
            
            if not es_duena and sucursal and empleado.sucursal != sucursal:
                messages.error(request, '🚫 No tienes permiso para asignar turnos a personal de otra sucursal.')
                return redirect('Personal:personal')

            Turno.objects.update_or_create(
                empleado=empleado,
                fecha=fecha,
                defaults={
                    'tipo_turno': tipo_turno,
                    'hora_inicio': hora_inicio,
                    'hora_fin': hora_fin,
                    'notas': notes,
                    'sucursal': sucursal or empleado.sucursal,
                    'creado_por': request.user
                }
            )
            
            messages.success(request, f'✅ Turno programado para {empleado.usuario.get_full_name()}')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
        
        return redirect('Personal:personal')
    
    empleados = Empleado.objects.all().select_related('usuario', 'sucursal')
    # ── FILTRO DINÁMICO ──
    if sucursal:
        empleados = empleados.filter(sucursal=sucursal)
    
    context = {
        'empleados': empleados,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/programar_turno.html', context)


@login_required(login_url='/')
@gerente_o_superior
def eliminar_turno(request, turno_id):
    """Eliminar un turno programado de forma segura en la sucursal activa."""
    turno = get_object_or_404(Turno, id=turno_id)
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal = getattr(request, 'sucursal_actual', None)
    es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))
    
    if not es_duena and sucursal and turno.sucursal != sucursal:
        messages.error(request, '🚫 No puedes eliminar turnos de otra sucursal.')
        return redirect('Personal:personal')

    turno.delete()
    messages.success(request, '✅ Turno eliminado')
    return redirect('Personal:personal')


# ==========================================
# VISTAS DE ASISTENCIA Y JUSTIFICANTES
# ==========================================

@login_required(login_url='/')
@cualquier_rol
def marcar_asistencia(request):
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
        
        if accion == 'dia_descanso':
            dia_seleccionado = request.POST.get('dia_descanso_semanal')
            if dia_seleccionado is not None:
                try:
                    empleado.dia_descanso_semanal = int(dia_seleccionado)
                    empleado.save()
                    messages.success(request, "✅ Tu día de descanso semanal se ha actualizado correctamente.")
                except ValueError:
                    messages.error(request, "❌ El día seleccionado no es válido.")
            return redirect('Personal:asistencia')

        elif accion == 'entrada':
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
                messages.success(request, f'✅ Salida registrada. Total trabajado: {asistencia.horas_trabajadas} hrs')
        
        elif accion == 'justificante':
            form_just = JustificanteForm(request.POST, request.FILES, instance=asistencia)
            if form_just.is_valid():
                inst         = form_just.save(commit=False)
                inst.estado  = 'ausente'
                inst.save()
                messages.success(request, '✅ Justificante subido correctamente.')
        
        return redirect('Personal:asistencia')

    historial_asistencias = Asistencia.objects.filter(
        empleado=empleado
    ).order_by('-fecha')[:10]

    context = {
        'asistencia':    asistencia,
        'form_entrada':  MarcarEntradaForm(initial={'hora_entrada': timezone.now().strftime('%H:%M')}),
        'form_salida':   MarcarSalidaForm(initial={'hora_salida':  timezone.now().strftime('%H:%M')}),
        'form_just':     JustificanteForm(instance=asistencia),
        'historial':     historial_asistencias,
        'dias_semana':   Empleado.DIAS_SEMANA,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/asistencia_empleado.html', context)


@login_required(login_url='/')
@gerente_o_superior
def tabla_asistencias(request):
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal = getattr(request, 'sucursal_actual', None)
    hoy_local = timezone.now().date()
    fecha_str = request.GET.get('fecha', hoy_local.isoformat())
    empleado_id = request.GET.get('empleado', '')

    try:
        fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        fecha_filtro = hoy_local

    asistencias = Asistencia.objects.select_related(
        'empleado__usuario', 'empleado__sucursal'
    ).filter(fecha=fecha_filtro)

    # ── FILTRO DINÁMICO ──
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

    presentes   = asistencias.filter(estado='presente').count()
    ausentes    = asistencias.filter(estado='ausente').count()
    descansos   = asistencias.filter(es_dia_descanso=True).count()

    empleados_qs = Empleado.objects.select_related('usuario')
    # ── FILTRO DINÁMICO ──
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
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/asistencias_admin.html', context)


@login_required(login_url='/')
@cualquier_rol
def subir_justificante(request):
    try:
        empleado = request.user.empleado
    except Exception:
        messages.error(request, '❌ Tu usuario no tiene perfil de empleado.')
        return redirect('PanelControl:panel')
    
    if request.method == 'POST':
        form = JustificanteCreateForm(request.POST, request.FILES)
        if form.is_valid():
            justificante = form.save(commit=False)
            justificante.empleado = empleado
            try:
                asistencia = Asistencia.objects.get(empleado=empleado, fecha=justificante.fecha)
                justificante.asistencia = asistencia
            except Asistencia.DoesNotExist:
                pass
            justificante.save()
            messages.success(request, '✅ Justificante enviado. Pendiente de revisión.')
            return redirect('Personal:mis_justificantes')
    else:
        form = JustificanteCreateForm()
    
    justificantes = Justificante.objects.filter(empleado=empleado).order_by('-fecha_creacion')
    context = {
        'form': form,
        'justificantes': justificantes,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/justificantes_empleado.html', context)


@login_required(login_url='/')
@cualquier_rol
def mis_justificantes(request):
    try:
        empleado = request.user.empleado
    except Exception:
        messages.error(request, '❌ Tu usuario no tiene perfil de empleado.')
        return redirect('PanelControl:panel')
    
    justificantes = Justificante.objects.filter(empleado=empleado).order_by('-fecha_creacion')
    context = {
        'justificantes': justificantes,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/mis_justificantes.html', context)


@login_required(login_url='/')
@gerente_o_superior
def control_justificantes(request):
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal = getattr(request, 'sucursal_actual', None)
    estado_filtro = request.GET.get('estado', 'pendiente')
    justificantes = Justificante.objects.select_related(
        'empleado__usuario', 'empleado__sucursal', 'revisado_por'
    ).all()
    
    # ── FILTRO DINÁMICO ──
    if sucursal:
        justificantes = justificantes.filter(empleado__sucursal=sucursal)
    if estado_filtro:
        justificantes = justificantes.filter(estado=estado_filtro)
    
    justificantes = justificantes.order_by('-fecha_creacion')
    context = {
        'justificantes': justificantes,
        'total': justificantes.count(),
        'pendientes': justificantes.filter(estado='pendiente').count(),
        'aprobados': justificantes.filter(estado='aprobado').count(),
        'rechazados': justificantes.filter(estado='rechazado').count(),
        'estado_filtro': estado_filtro,
        'usuario_nombre': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'Personal/control_justificantes.html', context)


@login_required(login_url='/')
@gerente_o_superior
def revisar_justificante(request, justificante_id):
    justificante = get_object_or_404(Justificante, id=justificante_id)
    
    # ── MODIFICACIÓN: Leer directamente del Middleware ──
    sucursal = getattr(request, 'sucursal_actual', None)
    es_duena = (request.user.is_superuser or (hasattr(request.user, 'rol') and request.user.rol in ['duena', 'dueña']))

    if not es_duena and sucursal and justificante.empleado.sucursal != sucursal:
        messages.error(request, '🚫 No tienes permiso para revisar este justificante.')
        return redirect('Personal:control_justificantes')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        comentario = request.POST.get('comentario', '')
        
        if accion == 'aprobar':
            justificante.aprobar(request.user, comentario)
            
            Notificacion.create_notificacion(
                usuario=justificante.empleado.usuario,
                tipo='success',
                titulo='Justificante Aprobado',
                detalle=f'Tu justificante del {justificante.fecha} ha sido aprobado.',
                icono='check_circle',
                color='text-secondary',  
                url='/personal/mis-justificantes/'
            )
            
            try:
                send_mail(
                    subject='✅ Justificante Aprobado - Enlace Don Chuy',
                    message=f'Hola {justificante.empleado.usuario.first_name},\n\n'
                        f'Tu justificante del {justificante.fecha} ha sido APROBADO.\n\n'
                        f'Motivo: {justificante.get_motivo_display()}\n'
                        f'Comentario: {comentario}\n\n'
                        f'Saludos,\nEquipo Enlace Don Chuy',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[justificante.empleado.usuario.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error enviando email: {e}")
            
            messages.success(request, '✅ Justificante aprobado y notificado.')
            
        elif accion == 'rechazar':
            justificante.rechazar(request.user, comentario)
            
            Notificacion.create_notificacion(
                usuario=justificante.empleado.usuario,
                tipo='error',
                titulo='Justificante Rechazado',
                detalle=f'Tu justificante del {justificante.fecha} ha sido rechazado. Motivo: {comentario}',
                icono='error',
                color='text-error',
                url='/personal/mis-justificantes/'
            )
            
            try:
                send_mail(
                    subject='❌ Justificante Rechazado - Enlace Don Chuy',
                    message=f'Hola {justificante.empleado.usuario.first_name},\n\n'
                        f'Tu justificante del {justificante.fecha} ha sido RECHAZADO.\n\n'
                        f'Motivo: {justificante.get_motivo_display()}\n'
                        f'Comentario: {comentario}\n\n'
                        f'Por favor, contacta a tu gerente para más información.\n\n'
                        f'Saludos,\nEquipo Enlace Don Chuy',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[justificante.empleado.usuario.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Error enviando email: {e}")
            
            messages.warning(request, '❌ Justificante rechazado y notificado.')
            
    return redirect('Personal:control_justificantes')




