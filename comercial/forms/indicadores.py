from django import forms
from comercial.models.indicadores import MetaFaturamento

class MetaFaturamentoForm(forms.ModelForm):
    class Meta:
        model = MetaFaturamento
        fields = ["ano", "mes", "valor"]
        widgets = {
            "ano": forms.NumberInput(attrs={"class": "form-control", "min": 2000, "max": 2100}),
            "mes": forms.Select(attrs={"class": "form-select"}),
            "valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        labels = {
            "ano": "Ano",
            "mes": "Mês",
            "valor": "Valor da Meta (R$)",
        }
        help_texts = {
            "ano": "Informe o ano da meta de faturamento.",
            "mes": "Selecione o mês da meta de faturamento.",
            "valor": "Informe o valor da meta de faturamento para o mês selecionado.",
        }
        