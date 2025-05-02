# qualidade_fornecimento/forms/f045_form.py
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple

from django import forms
from qualidade_fornecimento.models.f045 import RelatorioF045


class RelatorioF045Form(forms.ModelForm):
    qtd_carreteis = forms.IntegerField(
        required=False,
        label="Qtd Carretéis",
        widget=forms.NumberInput(attrs={"placeholder": "Ex: 5", "class": "form-control"})
    )

    class Meta:
        model = RelatorioF045
        fields = [
            "qtd_carreteis",
            "pedido_compra",
            "resistencia_tracao",
            "escoamento",
            "alongamento",
            "estriccao",
            "torcao_certificado",
            "dureza_certificado",
            "observacoes",
        ]
        widgets = {
            "pedido_compra": forms.TextInput(attrs={"class": "form-control"}),
            "resistencia_tracao": forms.TextInput(attrs={"class": "form-control text-center"}),
            "escoamento": forms.TextInput(attrs={"class": "form-control text-center"}),
            "alongamento": forms.TextInput(attrs={"class": "form-control text-center"}),
            "estriccao": forms.TextInput(attrs={"class": "form-control text-center"}),
            "torcao_certificado": forms.TextInput(attrs={"class": "form-control text-center"}),
            "dureza_certificado": forms.TextInput(attrs={"class": "form-control text-center"}),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observações sobre a aprovação condicional...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.limites: Dict[str, Tuple[Decimal, Decimal]] = kwargs.pop("limites_quimicos", {})
        super().__init__(*args, **kwargs)

        for sigla, (vmin, vmax) in self.limites.items():
            campo = f"{sigla}_user"
            self.fields[campo] = forms.DecimalField(
                label=sigla.upper(),
                required=False,
                max_digits=6,
                decimal_places=3,
                widget=forms.NumberInput(
                    {
                        "step": "0.001",
                        "class": "form-control text-center encontrado-input",
                    }
                ),
            )
            if getattr(self.instance, campo, None) is not None:
                self.fields[campo].initial = getattr(self.instance, campo)

    def clean(self):
        cleaned = super().clean()

        if self.data.get("switchStatusManual") == "on":
            return cleaned

        for sigla, (vmin, vmax) in self.limites.items():
            campo = f"{sigla}_user"
            valor_raw = self.data.get(campo)

            try:
                valor = Decimal(str(valor_raw).replace(",", ".")) if valor_raw not in [None, ""] else None
            except (InvalidOperation, TypeError, ValueError, AttributeError):
                valor = None

            if any(v is None for v in (valor, vmin, vmax)):
                continue


            if not (vmin <= valor <= vmax):

                self.add_error(
                    campo,
                    f"{sigla.upper()} fora do intervalo {vmin:g} – {vmax:g} %",
                )


        return cleaned

    def save(self, commit=True):
        inst: RelatorioF045 = super().save(commit=False)
        for sigla in self.limites:
            setattr(inst, f"{sigla}_user", self.cleaned_data.get(f"{sigla}_user"))
        if commit:
            inst.save(limites_quimicos=self.limites)
        return inst
