from django import forms
from .models import CierreCaja

INPUT_NUM = (
    'w-full bg-surface-container-low border-none rounded-xl '
    'py-8 pl-14 pr-8 text-5xl font-black text-primary '
    'focus:ring-2 focus:ring-primary '
    'focus:bg-surface-container-lowest transition-all '
    'placeholder:text-surface-container-highest'
)

SELECT_CLS = (
    'w-full bg-surface-container-high border-none rounded-xl '
    'py-3 px-4 text-on-surface focus:ring-2 '
    'focus:ring-primary font-body'
)

TEXTAREA_CLS = (
    'w-full bg-surface-container-high border-none rounded-xl '
    'py-3 px-4 text-on-surface focus:ring-2 '
    'focus:ring-primary resize-none font-body'
)


class CierreCajaForm(forms.ModelForm):
    class Meta:
        model = CierreCaja

        fields = [
            'turno',
            'efectivo_real',
            'notas',
        ]

        widgets = {
            'turno': forms.Select(
                choices=[
                    ('matutino', '☀️ Turno Matutino'),
                    ('vespertino', '🌙 Turno Vespertino'),
                ],
                attrs={
                    'class': SELECT_CLS,
                }
            ),

            'efectivo_real': forms.NumberInput(
                attrs={
                    'class': INPUT_NUM,
                    'placeholder': '0.00',
                    'step': '0.01',
                    'min': '0',
                    'id': 'efectivo_real',
                    'required': True,
                }
            ),

            'notas': forms.Textarea(
                attrs={
                    'class': TEXTAREA_CLS,
                    'rows': 3,
                    'placeholder': 'Observaciones del turno...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['turno'].choices = [
            ('matutino', '☀️ Turno Matutino'),
            ('vespertino', '🌙 Turno Vespertino'),
        ]







