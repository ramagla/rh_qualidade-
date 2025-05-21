from django import forms
from portaria.models import VeiculoPortaria

class VeiculoPortariaForm(forms.ModelForm):
    class Meta:
        model = VeiculoPortaria
        fields = ['placa', 'tipo', 'pessoa']
        widgets = {
            'pessoa': forms.Select(attrs={'class': 'form-select select2'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
        }
