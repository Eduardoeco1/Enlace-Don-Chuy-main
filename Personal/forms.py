from django import forms
from django.contrib.auth import get_user_model
from .models import Empleado, Asistencia, Justificante
from Inventario.models import Sucursal

# Estilos de Enlace Don Chuy
INPUT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'
INPUT_TIME = 'bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT_CLS_ASIST = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'

User = get_user_model()

class EmpleadoForm(forms.Form):
    """Formulario para la creación de nuevos empleados y sus usuarios."""
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Nombre de usuario'})
    )
    first_name = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        label='Apellido',
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': 'Apellido'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': INPUT, 'placeholder': 'correo@ejemplo.com'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': INPUT, 'placeholder': '••••••••'})
    )
    
    rol = forms.ChoiceField(
        choices=Empleado.ROLES_CHOICES,
        label='Rol',
        widget=forms.Select(attrs={'class': SELECT})
    )
    
    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.all(),
        label='Sucursal',
        widget=forms.Select(attrs={'class': SELECT})
    )
    
    estado = forms.ChoiceField(
        choices=Empleado.ESTADO_CHOICES,
        label='Estado inicial',
        initial='offline',
        widget=forms.Select(attrs={'class': SELECT})
    )
    
    telefono = forms.CharField(
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={'class': INPUT, 'placeholder': '+52 ...'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este email.')
        return email


class MarcarEntradaForm(forms.Form):
    """Formulario rápido para marcar entrada."""
    hora_entrada = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type':  'time',
        }),
        required=True,
    )


class MarcarSalidaForm(forms.Form):
    """Formulario rápido para marcar salida."""
    hora_salida = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type':  'time',
        }),
        required=True,
    )


class JustificanteForm(forms.ModelForm):
    """Formulario para añadir notas a una asistencia (sin archivo directo)."""
    class Meta:
        model  = Asistencia
        fields = ['notas'] # Corregido: Se eliminó 'justificante' que no existe en el modelo
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 3,
                'placeholder': 'Motivo de la ausencia o notas adicionales...',
            }),
        }


class AsistenciaAdminForm(forms.ModelForm):
    """Formulario para que el admin registre o edite asistencia de forma completa."""
    class Meta:
        model  = Asistencia
        fields = ['empleado', 'fecha', 'hora_entrada', 'hora_salida',
                  'estado', 'es_dia_descanso', 'notas'] # Corregido: Se eliminó 'justificante'
        widgets = {
            'empleado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'fecha': forms.DateInput(attrs={'class': INPUT_TIME, 'type': 'date'}),
            'hora_entrada': forms.TimeInput(attrs={'class': INPUT_TIME, 'type': 'time'}),
            'hora_salida': forms.TimeInput(attrs={'class': INPUT_TIME, 'type': 'time'}),
            'estado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 2,
            }),
        }


class JustificanteCreateForm(forms.ModelForm):
    """Formulario para que los empleados suban sus justificantes oficiales (con archivo)."""
    class Meta:
        model = Justificante
        fields = ['fecha', 'motivo', 'descripcion', 'archivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': INPUT}),
            'motivo': forms.Select(attrs={'class': SELECT}),
            'descripcion': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'placeholder': 'Detalla el motivo de tu ausencia...'
            }),
            'archivo': forms.FileInput(attrs={'class': 'w-full text-on-surface'}),
        }





        