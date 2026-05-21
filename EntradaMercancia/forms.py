from django import forms
from .models import EntradaInsumo
from Sucursales.models import Sucursal


class EntradaInsumoForm(forms.ModelForm):
    """
    Formulario para registrar entradas de mercancía.
    Implementa:
    1. Renderizado de producto como un menú desplegable (Select).
    2. Restricción visual y física de la sucursal para Gerentes (HiddenInput / Disabled).
    3. Acceso total a selección de sucursales para Dueña/Superusuario.
    """
    
    class Meta:
        model = EntradaInsumo
        fields = ['producto', 'categoria', 'cantidad', 'unidad', 'fecha_entrada', 'sucursal', 'notas']
        widgets = {
            # Se cambia a Select para renderizar de manera nativa el catálogo del Dropdown
            'producto': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'categoria': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
                'step': '0.01',
                'min': '0'
            }),
            'unidad': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
            }),
            'fecha_entrada': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500'
            }),
            'sucursal': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500'
            }),
            'notas': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500',
                'placeholder': 'Notas adicionales (opcional)'
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
        # Extraer parámetros personalizados pasados de forma segura desde la vista
        user = kwargs.pop('user', None)
        sucursal_actual = kwargs.pop('sucursal_actual', None)
        
        super().__init__(*args, **kwargs)
        
        # Evaluar el rol del usuario (Dueña o Superusuario) de forma robusta
        es_duena = False
        if user:
            es_duena = (
                user.is_superuser or 
                (hasattr(user, 'rol') and user.rol == 'duena') or 
                user.groups.filter(name='Dueña').exists()
            )
            
        # REGLA 1: Si NO es dueña (es Gerente o Empleado), se bloquea y oculta la sucursal
        if not es_duena:
            self.fields['sucursal'].disabled = True
            self.fields['sucursal'].widget = forms.HiddenInput()
            self.fields['sucursal'].required = False
            
            # Dejar preseleccionada la sucursal asignada del contexto
            if sucursal_actual:
                self.fields['sucursal'].initial = sucursal_actual
                
        # Si es dueña, puede ver todas las sucursales, pero sugerimos la actual del contexto
        elif sucursal_actual and not self.index_data_has_sucursal(*args):
            self.fields['sucursal'].initial = sucursal_actual

    def index_data_has_sucursal(self, *args):
        """Helper para verificar si el request POST ya contiene datos cargados de sucursal"""
        if args and args[0]:
            return 'sucursal' in args[0]
        return False
    


    