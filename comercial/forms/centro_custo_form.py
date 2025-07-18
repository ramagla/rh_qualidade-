from django import forms
from comercial.models.centro_custo import CentroDeCusto

class CentroDeCustoForm(forms.ModelForm):
    class Meta:
        model = CentroDeCusto
        fields = '__all__'
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Digite o nome do centro de custo"}),
            "custo_atual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vigencia": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d"
            ),
        }
