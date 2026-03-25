from django.forms import ModelForm, TextInput, NumberInput, Select, ValidationError
from .models import *


class ProductosForm(ModelForm):
    class Meta:
        model = Producto
        labels = {
            'id_iva':'IVA',
        }
        exclude = ['id_producto','usuario_creacion','usuario_modificacion','fecha_modificacion']
        widgets = {
            'nombre': TextInput(attrs={
                'class':'form-control',
                'placeholder': 'Ingrese el nombre del producto',
                'aria-label': 'Nombre de producto'
            }),
            'precio_actual':NumberInput(attrs={
                'class':'form-control',
                'placeholder': 'Ingrese el precio actual',
                'min':1,
                'aria-label': 'Precio actual'
            }),
            'costo_actual': NumberInput(attrs={
                'class':'form-control',
                'placeholder': 'Ingrese el costo actual',
                'min':1
            }),
            'stock_actual': NumberInput(attrs={
                'class':'form-control',
                'placeholder': 'Ingrese el stock actual',
                'min':0
            }),
            'stock_minimo': NumberInput(attrs={
                'class':'form-control',
                'placeholder': 'Ingrese el stock minimo',
                'min':0
            }),
            'id_iva': Select(attrs={
                'class':'form-control',}),
        }
    
    def clean_nombre(self):
        """
        Validamos que el nombre del producto a crear
        no se encuentre en uso
        """
        nombre = self.cleaned_data['nombre']

        instance = self.instance
        queryset = Producto.objects.filter(nombre=nombre).exclude(id_producto=instance.id_producto)
        
        if queryset.exists():
            raise ValidationError('El nombre ya existe!')
        return nombre
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_iva'].empty_label = 'Seleccione un IVA'
