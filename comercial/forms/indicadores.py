from django import forms
from decimal import Decimal, InvalidOperation
from comercial.models.indicadores import MetaFaturamento

class MetaFaturamentoForm(forms.ModelForm):
    class Meta:
        model = MetaFaturamento
        fields = ["ano", "mes", "valor"]
        widgets = {
            "ano": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 2000,
                "max": 2100
            }),
            "mes": forms.Select(attrs={"class": "form-select"}),
            # ⚠️ força type="text" para não bloquear vírgula/ponto
            "valor": forms.TextInput(attrs={
                "class": "form-control",
                "type": "text",
                "inputmode": "decimal",
                "autocomplete": "off",
                "placeholder": "ex.: 1.000.000,00",
                "pattern": r"[\d\.\,]*",
            }),
        }
        labels = {
            "ano": "Ano",
            "mes": "Mês",
            "valor": "Valor da Meta (R$)",
        }

    def clean_valor(self):
        v = self.cleaned_data.get("valor")
        if v is None or v == "":
            return v
        if isinstance(v, (int, float, Decimal)):
            return Decimal(v)
        s = str(v).strip()
        s = s.replace(".", "").replace(",", ".")
        try:
            return Decimal(s)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Informe um valor monetário válido.")
