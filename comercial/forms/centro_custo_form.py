from django import forms
from comercial.models.centro_custo import CentroDeCusto

class CentroDeCustoForm(forms.ModelForm):
    class Meta:
        model = CentroDeCusto
        fields = ["departamento", "custo_atual", "vigencia", "observacao"]
        widgets = {
            "departamento": forms.Select(attrs={"class": "form-select select2"}),
            "custo_atual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vigencia": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observacao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
