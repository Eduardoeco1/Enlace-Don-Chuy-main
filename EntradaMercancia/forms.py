from django import forms
from .models import EntradaInsumo

# Clase CSS reutilizable para mantener el diseño elegante
INPUT_CLASS    = 'w-full bg-surface-container-high border-none rounded-xl py-4 px-4 text-on-surface focus:ring-2 focus:ring-primary-container font-body'
SELECT_CLASS   = 'w-full bg-surface-container-high border-none rounded-xl py-4 px-4 text-on-surface focus:ring-2 focus:ring-primary-container appearance-none font-body'
TEXTAREA_CLASS = 'w-full bg-surface-container-high border-none rounded-xl py-4 px-4 text-on-surface focus:ring-2 focus:ring-primary-container font-body resize-none'

PRODUCTOS = [
    ('', 'Seleccione un insumo...'),
    ('Pollo',                       'Pollo'),
    ('Cabeza',                      'Cabeza'),
    ('Patitas',                     'Patitas'),
    ('Alitas',                      'Alitas'),
    ('Salchichas',                  'Salchichas'),
    ('Tacos',                       'Tacos'),
    ('Arroz',                       'Arroz'),
    ('Chiltepin',                   'Chiltepin'),
    ('Salsas',                      'Salsas'),
    ('Chile en polvo sasonador',    'Chile en polvo sasonador'),
    ('Chile en polvo',              'Chile en polvo'),
    ('Condimiento',                 'Condimiento'),
   
]

class EntradaInsumoForm(forms.ModelForm):
    producto = forms.ChoiceField(
        choices=PRODUCTOS,
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )

    class Meta:
        model  = EntradaInsumo
        fields = ['producto', 'cantidad', 'unidad', 'fecha_entrada', 'sucursal', 'notas']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'flex-1 bg-surface-container-high border-none rounded-xl py-4 px-4 text-on-surface text-right focus:ring-2 focus:ring-primary-container font-body',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'unidad': forms.TextInput(attrs={
                'class': 'bg-surface-container-high px-4 flex items-center justify-center rounded-xl text-xs font-bold text-on-surface-variant uppercase w-20 text-center',
                'value': 'KG',
            }),
            'fecha_entrada': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'sucursal': forms.Select(attrs={
                'class': SELECT_CLASS,
            }),
            'notas': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Detalles sobre el estado del producto, proveedor o incidencias...',
            }),
        }
        labels = {
            'cantidad':      'Cantidad',
            'unidad':        'Unidad',
            'fecha_entrada': 'Fecha de Entrada',
            'sucursal':      'Sucursal de Destino',
            'notas':         'Notas de Recepción',
        }
        