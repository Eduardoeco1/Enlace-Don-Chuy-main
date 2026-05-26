from django import forms
from django.contrib.auth import get_user_model
from .models import Empleado, Asistencia, Justificante
from Inventario.models import Sucursal
import re

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
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Nombre de usuario',
            'pattern': '[A-Za-z0-9_]+',
            'title': 'Solo letras, números y guion bajo',
        })
    )

    first_name = forms.CharField(
        label='Nombre',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Nombre',
            'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
            'title': 'Solo letras y espacios',
            'oninput': "this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ ]/g, '')"
        })
    )

    last_name = forms.CharField(
        label='Apellido',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Apellido',
            'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
            'title': 'Solo letras y espacios',
            'oninput': "this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ ]/g, '')"
        })
    )

    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': INPUT,
            'placeholder': 'correo@ejemplo.com'
        })
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': INPUT,
            'placeholder': '••••••••'
        })
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
        max_length=10,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': '2221234567',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[0-9]{10}',
            'title': 'Ingresa exactamente 10 números',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0,10)"
        })
    )

    # =========================
    # VALIDACIONES BACKEND
    # =========================

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Este nombre de usuario ya está en uso.'
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Ya existe un usuario registrado con este email.'
            )

        return email

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name')

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombre):
            raise forms.ValidationError(
                'El nombre solo puede contener letras y espacios.'
            )

        return nombre.strip()

    def clean_last_name(self):
        apellido = self.cleaned_data.get('last_name')

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', apellido):
            raise forms.ValidationError(
                'El apellido solo puede contener letras y espacios.'
            )

        return apellido.strip()

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')

        if not telefono:
            return telefono

        if not telefono.isdigit():
            raise forms.ValidationError(
                'El teléfono solo puede contener números.'
            )

        if len(telefono) != 10:
            raise forms.ValidationError(
                'El teléfono debe tener exactamente 10 dígitos.'
            )

        return telefono


class MarcarEntradaForm(forms.Form):
    """Formulario rápido para marcar entrada."""
    hora_entrada = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type': 'time',
        }),
        required=True,
    )


class MarcarSalidaForm(forms.Form):
    """Formulario rápido para marcar salida."""
    hora_salida = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type': 'time',
        }),
        required=True,
    )


class JustificanteForm(forms.ModelForm):
    """Formulario para añadir notas a una asistencia."""

    class Meta:
        model = Asistencia
        fields = ['notas']

        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 3,
                'placeholder': 'Motivo de la ausencia o notas adicionales...',
            }),
        }


class AsistenciaAdminForm(forms.ModelForm):
    """Formulario para que el admin registre o edite asistencia."""

    class Meta:
        model = Asistencia

        fields = [
            'empleado',
            'fecha',
            'hora_entrada',
            'hora_salida',
            'estado',
            'es_dia_descanso',
            'notas'
        ]

        widgets = {
            'empleado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'fecha': forms.DateInput(attrs={
                'class': INPUT_TIME,
                'type': 'date'
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'class': INPUT_TIME,
                'type': 'time'
            }),
            'hora_salida': forms.TimeInput(attrs={
                'class': INPUT_TIME,
                'type': 'time'
            }),
            'estado': forms.Select(attrs={'class': SELECT_CLS_ASIST}),
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 2,
            }),
        }


class JustificanteCreateForm(forms.ModelForm):
    """Formulario para subir justificantes oficiales."""

    class Meta:
        model = Justificante

        fields = [
            'fecha',
            'motivo',
            'descripcion',
            'archivo'
        ]

        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT
            }),

            'motivo': forms.Select(attrs={
                'class': SELECT
            }),

            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'placeholder': 'Detalla el motivo de tu ausencia...'
            }),

            'archivo': forms.FileInput(attrs={
                'class': 'w-full text-on-surface'
            }),
        }




        