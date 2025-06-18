from django import forms
from tecnico.models.roteiro import InsumoEtapa
from django.forms import Select, NumberInput, CheckboxInput

class InsumoForm(forms.ModelForm):
    class Meta:
        model = InsumoEtapa
        fields = ['materia_prima', 'quantidade', 'tipo_insumo', 'obrigatorio']
        widgets = {
            'insumo': Select(attrs={'class': 'form-select select2'}),
            'quantidade': NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'tipo_insumo': Select(attrs={'class': 'form-select'}),
            'obrigatorio': CheckboxInput(attrs={'class': 'form-check-input'}),
            'materia_prima': Select(attrs={'class': 'form-select select2'}),

        }
