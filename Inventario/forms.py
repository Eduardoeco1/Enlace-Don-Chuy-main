from django import forms
from .models import Producto

INPUT_CLASS = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
SELECT_CLASS = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary appearance-none font-body'

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'sucursal', 'stock', 'unidad', 'stock_minimo', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nombre del producto'}),
            'categoria': forms.Select(attrs={'class': SELECT_CLASS}),
            'sucursal': forms.Select(attrs={'class': SELECT_CLASS, 'required': 'required'}),
            'stock': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1', 'placeholder': '0.0'}),
            'unidad': forms.Select(attrs={'class': SELECT_CLASS}),
            'stock_minimo': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1', 'placeholder': '10.0'}),
        }

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.fields['sucursal'].required = True
    self.fields['sucursal'].empty_label = "Selecciona una sucursal"