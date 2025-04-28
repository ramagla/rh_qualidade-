from django import forms
from django.forms import inlineformset_factory

from qualidade_fornecimento.models import FornecedorQualificado
from qualidade_fornecimento.models.controle_servico_externo import (
    ControleServicoExterno,
    RetornoDiario,
)
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


class ControleServicoExternoForm(forms.ModelForm):
    class Meta:
        model = ControleServicoExterno
        exclude = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos Select2
        self.fields["fornecedor"].queryset = (
            FornecedorQualificado.objects.all().order_by("nome")
        )
        self.fields["fornecedor"].widget.attrs.update(
            {
                "class": "form-select select2",
                "data-placeholder": "Selecione o fornecedor",
            }
        )

        self.fields["codigo_bm"].queryset = MateriaPrimaCatalogo.objects.filter(
            tipo="Tratamento"
        ).order_by("codigo")
        self.fields["codigo_bm"].widget.attrs.update(
            {
                "class": "form-select select2",
                "data-placeholder": "Selecione o Código BM",
            }
        )

        # Campos de data
        for date_field in ["data_envio", "data_retorno"]:
            if date_field in self.fields:
                self.fields[date_field].widget = forms.DateInput(
                    attrs={"type": "date", "class": "form-control"}
                )

        # Lead Time - Somente readonly, sem disabled
        self.fields["lead_time"].widget.attrs.update(
            {"readonly": "readonly", "class": "form-control bg-light"}
        )

        # IQF
        self.fields["iqf"].widget.attrs.update({"class": "form-select"})


class RetornoDiarioForm(forms.ModelForm):
    class Meta:
        model = RetornoDiario
        fields = ["data", "quantidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data"].widget = forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        )
        self.fields["quantidade"].widget.attrs.update({"class": "form-control"})


RetornoDiarioFormSet = inlineformset_factory(
    ControleServicoExterno,
    RetornoDiario,
    form=RetornoDiarioForm,
    extra=1,
    can_delete=True,
)
