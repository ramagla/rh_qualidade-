from decimal import Decimal
from typing import Dict, Tuple

from django import forms

from qualidade_fornecimento.models.f045 import RelatorioF045


class RelatorioF045Form(forms.ModelForm):
    # Se por algum motivo você ainda quisesse mantê‑lo no form, bastaria:
    # bitola = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = RelatorioF045
        fields = [
            # retirei "bitola" daqui
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
            "qtd_carreteis": forms.NumberInput(attrs={"class": "form-control"}),
            "pedido_compra": forms.TextInput(attrs={"class": "form-control"}),
            "resistencia_tracao": forms.TextInput(
                attrs={"class": "form-control text-center"}
            ),
            "escoamento": forms.TextInput(attrs={"class": "form-control text-center"}),
            "alongamento": forms.TextInput(attrs={"class": "form-control text-center"}),
            "estriccao": forms.TextInput(attrs={"class": "form-control text-center"}),
            "torcao_certificado": forms.TextInput(
                attrs={"class": "form-control text-center"}
            ),
            "dureza_certificado": forms.TextInput(
                attrs={"class": "form-control text-center"}
            ),
            "observacoes": forms.Textarea(
                {
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observações sobre a aprovação condicional...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        # recebe os limites via view
        self.limites: Dict[str, Tuple[Decimal, Decimal]] = kwargs.pop(
            "limites_quimicos", {}
        )
        super().__init__(*args, **kwargs)

        # geração dinâmica de campos *_user para composição
        for sigla, (vmin, vmax) in self.limites.items():
            campo = f"{sigla}_user"
            self.fields[campo] = forms.DecimalField(
                label=sigla.upper(),
                required=False,
                max_digits=7,
                decimal_places=4,
                widget=forms.NumberInput(
                    {
                        "step": "0.0001",
                        "class": "form-control text-center encontrado-input",
                    }
                ),
            )
            # valor inicial vindo da instância
            if getattr(self.instance, campo, None) is not None:
                self.fields[campo].initial = getattr(self.instance, campo)

    def clean(self):
        cleaned = super().clean()

        # se aprov. condicional, ignora validação dos limites
        if self.data.get("switchStatusManual") == "on":
            return cleaned

        # valida cada composição contra o seu limite
        for sigla, (vmin, vmax) in self.limites.items():
            valor = cleaned.get(f"{sigla}_user")
            # ignora N/A (0–0) ou valor vazio
            if valor is None or (vmin == 0 and vmax == 0):
                continue
            # Se vmin ou vmax são None, não valida — considera aprovado
            if vmin is None or vmax is None:
                continue
            if not (vmin <= valor <= vmax):
                self.add_error(
                    f"{sigla}_user",
                    f"{sigla.upper()} fora do intervalo {vmin:g} – {vmax:g} %",
                )


        return cleaned

    def save(self, commit=True):
        inst: RelatorioF045 = super().save(commit=False)
        # grava de volta cada *_user
        for sigla in self.limites:
            setattr(inst, f"{sigla}_user", self.cleaned_data.get(f"{sigla}_user"))
        if commit:
            inst.save(limites_quimicos=self.limites)
        return inst
