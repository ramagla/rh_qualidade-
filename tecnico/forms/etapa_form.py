from django import forms
from tecnico.models.roteiro import EtapaRoteiro

class EtapaRoteiroForm(forms.ModelForm):
    class Meta:
        model = EtapaRoteiro
        exclude = ("roteiro",)
        fields = ["etapa", "setor", "pph", "setup_minutos"]
        widgets = {
            "etapa": forms.NumberInput(attrs={"class": "form-control"}),
            "pph": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "setup_minutos": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }
