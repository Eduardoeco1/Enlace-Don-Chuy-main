from django import forms
from .models import EntradaInsumo


UNIDAD_CHOICES = [
    ('PZ', 'PZ - Pieza'),
    ('KG', 'KG - Kilogramos'),
    ('G', 'G - Gramos'),
    ('LT', 'LT - Litros'),
    ('ML', 'ML - Mililitros'),
    ('PAQ', 'PAQ - Paquete'),
    ('CJ', 'CJ - Caja'),
]


class EntradaInsumoForm(forms.ModelForm):
    class Meta:
        model = EntradaInsumo
        fields = [
            'producto',
            'categoria',
            'cantidad',
            'unidad',
            'fecha_entrada',
            'sucursal',
            'notas'
        ]

        widgets = {
            'producto': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
                'step': '1',
                'min': '1',
                'placeholder': 'Ej. 10',
            }),
            'unidad': forms.Select(
                choices=UNIDAD_CHOICES,
                attrs={
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
                }
            ),
            'fecha_entrada': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'sucursal': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'notas': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
                'placeholder': 'Notas adicionales (opcional)',
            }),
        }

        labels = {
            'producto': 'Nombre del Producto',
            'categoria': 'Categoría',
            'cantidad': 'Cantidad',
            'unidad': 'Unidad de Medida',
            'fecha_entrada': 'Fecha de Entrada',
            'sucursal': 'Sucursal',
            'notas': 'Notas',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        sucursal_actual = kwargs.pop('sucursal_actual', None)

        super().__init__(*args, **kwargs)

        self.fields['cantidad'].min_value = 1
        self.fields['unidad'].choices = UNIDAD_CHOICES

        es_duena = False

        if user:
            es_duena = (
                user.is_superuser or
                (hasattr(user, 'rol') and user.rol in ['duena', 'dueña']) or
                user.groups.filter(name='Dueña').exists()
            )

        if not es_duena:
            self.fields['sucursal'].disabled = True
            self.fields['sucursal'].widget = forms.HiddenInput()
            self.fields['sucursal'].required = False

            if sucursal_actual:
                self.fields['sucursal'].initial = sucursal_actual

        elif sucursal_actual and not self._post_tiene_sucursal(*args):
            self.fields['sucursal'].initial = sucursal_actual

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')

        if cantidad is None:
            return cantidad

        if cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a 0.')

        if cantidad != int(cantidad):
            raise forms.ValidationError('La cantidad debe ser un número entero.')

        return int(cantidad)

    def _post_tiene_sucursal(self, *args):
        if args and args[0]:
            return 'sucursal' in args[0]
        return False