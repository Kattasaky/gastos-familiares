from django import forms
from .models import ItemCompra

class ItemCompraForm(forms.ModelForm):
    class Meta:
        model = ItemCompra
        fields = ['nombre', 'cantidad', 'valor_aprox', 'categoria', 'frecuencia']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_aprox': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'frecuencia': forms.Select(attrs={'class': 'form-select'}),
        }
