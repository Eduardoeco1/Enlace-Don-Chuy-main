import re
from django import forms

from .models import Producto
from Sucursales.models import Sucursal


INPUT_CLASS = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT_CLASS = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'


UNIDAD_CHOICES = [
    ('PZ', 'PZ - Pieza'),
    ('KG', 'KG - Kilogramos'),
    ('G', 'G - Gramos'),
    ('LT', 'LT - Litros'),
    ('ML', 'ML - Mililitros'),
    ('PAQ', 'PAQ - Paquete'),
    ('CJ', 'CJ - Caja'),
]


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto

        fields = [
            'nombre',
            'categoria',
            'sucursal',
            'stock',
            'unidad',
            'stock_minimo',
            'imagen'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nombre del producto',
                'pattern': '[A-Za-zÁÉÍÓÚáéíóúÑñ ]+',
                'title': 'Solo letras y espacios',
                'maxlength': '100',
            }),

            'categoria': forms.Select(attrs={
                'class': SELECT_CLASS
            }),

            'sucursal': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),

            'stock': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '1',
                'min': '0',
                'placeholder': '0'
            }),

            'unidad': forms.Select(
                choices=UNIDAD_CHOICES,
                attrs={
                    'class': SELECT_CLASS
                }
            ),

            'stock_minimo': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '1',
                'min': '0',
                'placeholder': '10'
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        sucursal_actual = kwargs.pop('sucursal_actual', None)
        es_duena = kwargs.pop('es_duena', False)

        super().__init__(*args, **kwargs)

        self.fields['unidad'].choices = UNIDAD_CHOICES

        if es_duena:
            self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)
            self.fields['sucursal'].required = True
            self.fields['sucursal'].empty_label = 'Selecciona una sucursal'
        else:
            self.fields['sucursal'].required = False
            self.fields['sucursal'].widget = forms.HiddenInput()

            if sucursal_actual:
                self.fields['sucursal'].queryset = Sucursal.objects.filter(id=sucursal_actual.id)
                self.fields['sucursal'].initial = sucursal_actual

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()

        if not nombre:
            raise forms.ValidationError('El nombre del producto es obligatorio.')

        if not re.fullmatch(r'[A-Za-zÁÉÍÓÚáéíóúÑñ ]+', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')

        return nombre

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')

        if stock is None:
            return stock

        if stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')

        if stock != int(stock):
            raise forms.ValidationError('El stock debe ser un número entero.')

        return int(stock)

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')

        if stock_minimo is None:
            return stock_minimo

        if stock_minimo < 0:
            raise forms.ValidationError('El stock mínimo no puede ser negativo.')

        if stock_minimo != int(stock_minimo):
            raise forms.ValidationError('El stock mínimo debe ser un número entero.')

        return int(stock_minimo)
    