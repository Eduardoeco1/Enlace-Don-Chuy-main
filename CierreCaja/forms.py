from django import forms
from .models import CierreCaja

INPUT_NUM    = 'w-full bg-surface-container-low border-none rounded-xl py-8 pl-14 pr-8 text-5xl font-black text-primary focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all placeholder:text-surface-container-highest'
INPUT_FONDO  = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface text-right focus:ring-2 focus:ring-primary font-body text-lg font-bold'
INPUT_DENOM  = 'w-full border-none p-0 text-lg font-bold focus:ring-0 bg-transparent text-center'
SELECT_CLS   = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary font-body'
TEXTAREA_CLS = 'w-full bg-surface-container-high border-none rounded-xl py-3 px-4 text-on-surface focus:ring-2 focus:ring-primary resize-none font-body'

class CierreCajaForm(forms.ModelForm):
    class Meta:
        model  = CierreCaja
        fields = [
            'turno', 'fondo_inicial',
            'efectivo_real',
            # Billetes
            'billetes_1000', 'billetes_500', 'billetes_200',
            'billetes_100',  'billetes_50',  'billetes_20',
            # Monedas
            'monedas_10', 'monedas_5', 'monedas_2', 'monedas_1',
            'notas',
        ]
        widgets = {
            'turno': forms.Select(attrs={'class': SELECT_CLS}),
            'fondo_inicial': forms.NumberInput(attrs={
                'class': INPUT_FONDO,
                'step':  '0.01', 'min': '0',
                'id':    'fondo_inicial',
            }),
            'efectivo_real': forms.NumberInput(attrs={
                'class':       INPUT_NUM,
                'placeholder': '0.00',
                'step':        '0.01',
                'min':         '0',
                'id':          'efectivo_real',
            }),
            'billetes_1000': forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b1000'}),
            'billetes_500':  forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b500'}),
            'billetes_200':  forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b200'}),
            'billetes_100':  forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b100'}),
            'billetes_50':   forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b50'}),
            'billetes_20':   forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'b20'}),
            'monedas_10':    forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'm10'}),
            'monedas_5':     forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'm5'}),
            'monedas_2':     forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'm2'}),
            'monedas_1':     forms.NumberInput(attrs={'class': INPUT_DENOM, 'min': '0', 'id': 'm1'}),
            'notas': forms.Textarea(attrs={
                'class':       TEXTAREA_CLS,
                'rows':        3,
                'placeholder': 'Observaciones del turno...',
            }),
        }

