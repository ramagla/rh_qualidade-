from django import forms
from portaria.models.consumo_agua import RegistroConsumoAgua

class RegistroConsumoAguaForm(forms.ModelForm):
    class Meta:
        model = RegistroConsumoAgua
        fields = ["data", "leitura_inicial", "leitura_final", "observacao"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "leitura_inicial": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "leitura_final": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
