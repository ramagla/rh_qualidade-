from django import forms

from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


class MateriaPrimaCatalogoForm(forms.ModelForm):
    class Meta:
        model = MateriaPrimaCatalogo
        fields = [
            "codigo",
            "descricao",
            "localizacao",
            "classe",
            "norma",
            "bitola",
            "tipo",
            "tipo_abnt",
            "tolerancia",
            "tolerancia_largura",
            "largura",
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "localizacao": forms.TextInput(attrs={"class": "form-control"}),
            "classe": forms.TextInput(attrs={"class": "form-control"}),
            "norma": forms.TextInput(attrs={"class": "form-control"}),
            "bitola": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "tipo_abnt": forms.TextInput(attrs={"class": "form-control"}),
            "tolerancia": forms.TextInput(attrs={"class": "form-control"}),
            "tolerancia_largura": forms.TextInput(attrs={"class": "form-control"}),
            "largura": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_largura(self):
        valor = self.cleaned_data.get("largura")
        if not valor:
            return ""  # Se o campo estiver vazio, retorna vazio sem erro

        if isinstance(valor, str):
            valor = valor.replace(",", ".")

        try:
            return float(valor)
        except (TypeError, ValueError):
            raise forms.ValidationError(
                "Informe um número válido (ex: 43,30 ou 43.30)."
            )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")

        if tipo == "Tratamento":
            for campo in [
                "classe",
                "bitola",
                "norma",
                "localizacao",
                "tipo_abnt",
                "tolerancia",
                "tolerancia_largura",
                "largura",
            ]:
                cleaned_data[campo] = ""
        return cleaned_data
