from decimal import Decimal, InvalidOperation

from django import forms

from qualidade_fornecimento.models.rolo import RoloMateriaPrima


class RoloMateriaPrimaForm(forms.ModelForm):
    nro_rolo = forms.CharField(
        required=False,
        label="N° do Rolo",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly",
            "placeholder": "Será gerado ao salvar"
        }),
    )

    class Meta:
        model = RoloMateriaPrima
        fields = [
            "tb050",  # ✅ ESSENCIAL — é o que falta para o formset funcionar
            "nro_rolo",
            "peso",
            "bitola_espessura",
            "bitola_largura",
            "tracao",
            "dureza",
            "enrolamento",
            "dobramento",
            "torcao_residual",
            "aspecto_visual",
            "alongamento",
            "flechamento",
        ]
        widgets = {
            "tb050": forms.HiddenInput(),  # para não exibir — MAS OBRIGATÓRIO no formset
            "peso": forms.NumberInput(attrs={"class": "form-control text-center"}),
            "tracao": forms.HiddenInput(),
            "dureza": forms.HiddenInput(),
            "enrolamento": forms.Select(attrs={"class": "form-select text-center"}),
            "dobramento": forms.Select(attrs={"class": "form-select text-center"}),
            "torcao_residual": forms.Select(attrs={"class": "form-select text-center"}),
            "aspecto_visual": forms.Select(attrs={"class": "form-select text-center"}),
            "alongamento": forms.Select(attrs={"class": "form-select text-center"}),
            "flechamento": forms.Select(attrs={"class": "form-select text-center"}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance

        self.fields["nro_rolo"].initial = inst.nro_rolo or "Será gerado ao salvar"

        CHOICES = [("OK", "OK"), ("NOK", "NOK")]
        for nome in [
            "enrolamento",
            "dobramento",
            "torcao_residual",
            "aspecto_visual",
            "alongamento",
            "flechamento",
        ]:
            if nome in self.fields:
                self.fields[nome].choices = CHOICES
                self.fields[nome].initial = getattr(inst, nome, None)  # 🔥 garante que o valor salvo apareça

    def clean(self):
        cleaned = super().clean()

        # Conversão segura de vírgula para ponto nos campos numéricos
        for field in ["bitola_espessura", "bitola_largura", "tracao"]:
            value = cleaned.get(field)
            if value is not None and isinstance(value, str):
                try:
                    value = Decimal(value.replace(",", "."))
                    cleaned[field] = value
                except (InvalidOperation, AttributeError):
                    self.add_error(field, "Informe um número válido.")

        return cleaned