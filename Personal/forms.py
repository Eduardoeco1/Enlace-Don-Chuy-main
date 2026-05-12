from django import forms
from django.contrib.auth import get_user_model
from .models import Empleado, Asistencia
from Inventario.models import Sucursal

# Estilos de Enlace Don Chuy
INPUT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'
INPUT_TIME = 'bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT_CLS_ASIST = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'

User = get_user_model()

class EmpleadoForm(forms.Form):
    # Nuevo campo de Usuario independiente
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
        """Valida que el nombre de usuario no esté duplicado."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        """Valida que el correo sea único."""
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
    """Formulario para subir justificante."""
    class Meta:
        model  = Asistencia
        fields = ['justificante', 'notas']
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 3,
                'placeholder': 'Motivo de la ausencia...',
            }),
        }


class AsistenciaAdminForm(forms.ModelForm):
    """Formulario para que el admin registre/edite asistencia."""
    class Meta:
        model  = Asistencia
        fields = ['empleado', 'fecha', 'hora_entrada', 'hora_salida',
                  'estado', 'es_dia_descanso', 'justificante', 'notas']
        widgets = {
            'empleado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'fecha':    forms.DateInput(attrs={
                'class': INPUT_TIME, 'type': 'date'
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'class': INPUT_TIME, 'type': 'time'
            }),
            'hora_salida': forms.TimeInput(attrs={
                'class': INPUT_TIME, 'type': 'time'
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'notas':  forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 2,
            }),
        }




        