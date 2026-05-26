from django import forms
from django.contrib.auth import get_user_model
from .models import Empleado, Asistencia, Justificante
from Inventario.models import Sucursal
import re

# Estilos
INPUT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'
INPUT_TIME = 'bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT_CLS_ASIST = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'

User = get_user_model()


class EmpleadoForm(forms.Form):

    username = forms.CharField(
        label='Usuario',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Nombre de usuario',
            'pattern': '[A-Za-z0-9_]+',
        })
    )

    first_name = forms.CharField(
        label='Nombre',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Nombre',
            'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
            'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ ]/g,'')"
        })
    )

    last_name = forms.CharField(
        label='Apellido',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Apellido',
            'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
            'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ ]/g,'')"
        })
    )

    email = forms.EmailField(
        label='Correo',
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
        widget=forms.Select(attrs={'class': SELECT})
    )

    sucursal = forms.ModelChoiceField(
        queryset=Sucursal.objects.none(),
        widget=forms.Select(attrs={'class': SELECT})
    )

    estado = forms.ChoiceField(
        choices=Empleado.ESTADO_CHOICES,
        initial='offline',
        widget=forms.Select(attrs={'class': SELECT})
    )

    telefono = forms.CharField(
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': '2221234567',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[0-9]{10}',
            'oninput': "this.value=this.value.replace(/[^0-9]/g,'').slice(0,10)"
        })
    )

    # ==========================================
    # CONTROL MULTISUCURSAL
    # ==========================================

    def __init__(self, *args, **kwargs):
        sucursal_actual = kwargs.pop('sucursal_actual', None)
        es_duena = kwargs.pop('es_duena', False)

        super().__init__(*args, **kwargs)

        if es_duena:
            self.fields['sucursal'].queryset = Sucursal.objects.all()
        else:
            if sucursal_actual:
                self.fields['sucursal'].queryset = Sucursal.objects.filter(
                    id=sucursal_actual.id
                )

                self.fields['sucursal'].initial = sucursal_actual

    # ==========================================
    # VALIDACIONES
    # ==========================================

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Este nombre de usuario ya existe.'
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Ya existe un usuario con este correo.'
            )

        return email

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name')

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombre):
            raise forms.ValidationError(
                'El nombre solo puede contener letras.'
            )

        return nombre.strip()

    def clean_last_name(self):
        apellido = self.cleaned_data.get('last_name')

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', apellido):
            raise forms.ValidationError(
                'El apellido solo puede contener letras.'
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
    hora_entrada = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type': 'time',
        }),
        required=True,
    )


class MarcarSalidaForm(forms.Form):
    hora_salida = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': INPUT_TIME,
            'type': 'time',
        }),
        required=True,
    )


class JustificanteForm(forms.ModelForm):

    class Meta:
        model = Asistencia
        fields = ['notas']

        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body',
                'rows': 3,
            }),
        }


class AsistenciaAdminForm(forms.ModelForm):

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
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface resize-none font-body',
                'rows': 2,
            }),
        }


class JustificanteCreateForm(forms.ModelForm):

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
                'class': 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface resize-none font-body',
            }),

            'archivo': forms.FileInput(attrs={
                'class': 'w-full text-on-surface'
            }),
        }



        

        