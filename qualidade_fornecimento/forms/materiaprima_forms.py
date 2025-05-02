from django import forms
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.models.norma import NormaTecnica, NormaComposicaoElemento


class MateriaPrimaCatalogoForm(forms.ModelForm):
    norma = forms.ModelChoiceField(
    queryset=NormaTecnica.objects.all().order_by('nome_norma'),
    required=False,
    label='Norma',
    widget=forms.Select(attrs={"class": "form-select select2 select2-norma"})
)
    tipo_abnt = forms.ChoiceField(
    required=False,
    label='Tipo ABNT / Classe',
    choices=[],
    widget=forms.Select(attrs={
        "class": "form-select select2 select2-tipo-abnt",
        "id": "id_tipo_abnt"
    })
)


    class Meta:
        model = MateriaPrimaCatalogo
        fields = "__all__"
        
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "localizacao": forms.TextInput(attrs={"class": "form-control"}),
            "classe": forms.TextInput(attrs={"class": "form-control"}),
            "bitola": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "tolerancia": forms.TextInput(attrs={"class": "form-control"}),
            "tolerancia_largura": forms.TextInput(attrs={"class": "form-control"}),
            "largura": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_material": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Inox"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicialmente sem opções
        self.fields["tipo_abnt"].choices = [("", "---------")]

        # Se estiver preenchendo via POST (formulário com valor em 'norma')
        if "norma" in self.data:
            try:
                norma_id = int(self.data.get("norma"))
                tipos = (
                    NormaComposicaoElemento.objects.filter(norma_id=norma_id)
                    .exclude(tipo_abnt__isnull=True)
                    .exclude(tipo_abnt="")
                    .values_list("tipo_abnt", flat=True)
                    .distinct()
                    .order_by("tipo_abnt")
                )
                self.fields["tipo_abnt"].choices += [(t, t) for t in tipos]
            except (ValueError, TypeError):
                pass

        # Ou se for edição de um registro existente
        elif self.instance.pk and self.instance.norma:
            tipos = (
                NormaComposicaoElemento.objects.filter(norma=self.instance.norma)
                .exclude(tipo_abnt__isnull=True)
                .exclude(tipo_abnt="")
                .values_list("tipo_abnt", flat=True)
                .distinct()
                .order_by("tipo_abnt")
            )
            self.fields["tipo_abnt"].choices += [(t, t) for t in tipos]

    def clean_largura(self):
        valor = self.cleaned_data.get("largura")
        if not valor:
            return ""
        if isinstance(valor, str):
            valor = valor.replace(",", ".")
        try:
            return float(valor)
        except (TypeError, ValueError):
            raise forms.ValidationError("Informe um número válido (ex: 43,30 ou 43.30).")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("tipo") == "Tratamento":
            for campo in [
                "classe", "bitola", "norma", "localizacao", "tipo_abnt",
                "tolerancia", "tolerancia_largura", "largura"
            ]:
                if campo == "norma":
                    cleaned_data[campo] = None  # ForeignKey deve ser None
                else:
                    cleaned_data[campo] = ""
        return cleaned_data

