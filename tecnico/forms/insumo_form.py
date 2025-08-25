from django import forms
from tecnico.models.roteiro import InsumoEtapa
from django.forms import Select, NumberInput, CheckboxInput

class InsumoForm(forms.ModelForm):
    class Meta:
        model = InsumoEtapa
        fields = ['materia_prima', 'tipo_insumo', 'obrigatorio', 'desenvolvido', 'peso_liquido', 'peso_bruto']
        widgets = {
            'materia_prima': Select(attrs={'class': 'form-select select2'}),
            'tipo_insumo': Select(attrs={'class': 'form-select'}),
            'obrigatorio': CheckboxInput(attrs={'class': 'form-check-input'}),
            'desenvolvido': NumberInput(attrs={'class': 'form-control', 'step': 'any', 'inputmode': 'decimal'}),
            'peso_liquido': NumberInput(attrs={'class': 'form-control', 'step': 'any', 'inputmode': 'decimal'}),
            'peso_bruto':   NumberInput(attrs={'class': 'form-control', 'step': 'any', 'inputmode': 'decimal'}),
        }
