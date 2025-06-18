from django import forms
from tecnico.models.roteiro import PropriedadesEtapa

class PropriedadesEtapaForm(forms.ModelForm):
    class Meta:
        model = PropriedadesEtapa
        fields = ["nome_acao", "descricao_detalhada", "maquinas", "ferramenta"]
        widgets = {
            "nome_acao": forms.TextInput(attrs={"class": "form-control"}),
            "descricao_detalhada": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "maquinas": forms.SelectMultiple(attrs={"class": "form-select select2", "multiple": "multiple"}),
            "ferramenta": forms.Select(attrs={"class": "form-select select2"}),

        }
