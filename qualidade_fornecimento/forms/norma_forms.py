from django import forms
from django.forms.models import BaseModelFormSet

from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from qualidade_fornecimento.models.norma import (
    NormaComposicaoElemento,
    NormaTecnica,
    NormaTracao,
)

# =====================================================
# Classe base para formsets que remove o campo "id"
# e permite formulários extras vazios.
# =====================================================
class BaseEmptyModelFormSet(BaseModelFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)

        # ⚠️ Em vez de deletar o campo, ocultamos com HiddenInput para não quebrar o Django
        if "id" in form.fields:
            form.fields["id"].widget = forms.HiddenInput()

        # Permite que formulários extras sejam deixados em branco
        if i >= self.initial_form_count():
            form.empty_permitted = True

        return form


# ---------------------------------------------------------
# 1) Cabeçalho da Norma
# ---------------------------------------------------------
class NormaTecnicaForm(forms.ModelForm):
    nome_norma = forms.CharField(
        label="Nome da Norma",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: NBR-ISO 16120-1"}),
    )
    vinculo_norma = forms.CharField(
        label="Norma vinculada (tração)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: ASTM A580"}),
    )

    class Meta:
        model = NormaTecnica
        fields = ["nome_norma", "arquivo_norma", "vinculo_norma"]
        widgets = {
            "arquivo_norma": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_vinculo_norma(self):
        return self.cleaned_data.get("vinculo_norma")


# ---------------------------------------------------------
# 2) Composição Química
# ---------------------------------------------------------
class ComposicaoQuimicaForm(forms.ModelForm):
    tipo_abnt = forms.CharField(
        label="Tipo de Aço ABNT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 302"}),
    )

    class Meta:
        model = NormaComposicaoElemento
        element_fields = [
            "c_min", "c_max", "mn_min", "mn_max",
            "si_min", "si_max", "p_min", "p_max",
            "s_min", "s_max", "cr_min", "cr_max",
            "ni_min", "ni_max", "cu_min", "cu_max",
            "al_min", "al_max",
        ]
        fields = ["tipo_abnt", *element_fields]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fld in self.Meta.element_fields:
            self.fields[fld].required = False
            self.fields[fld].widget.attrs.update({"class": "form-control", "step": "0.001"})

    def clean(self):
        cleaned_data = super().clean()
        for fld in self.Meta.element_fields:
            if cleaned_data.get(fld) == "":
                cleaned_data[fld] = None
        return cleaned_data


# ---------------------------------------------------------
# 3) Faixa de Resistência à Tração
# ---------------------------------------------------------
class TracaoForm(forms.ModelForm):
    class Meta:
        model = NormaTracao
        fields = [
            "tipo_abnt", 
            "bitola_minima", "bitola_maxima",
            "resistencia_min", "resistencia_max",
            "dureza",
        ]
        widgets = {
            "tipo_abnt": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 1020"}),
            "bitola_minima": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Ex: 1,20"}),
            "bitola_maxima": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Ex: 3,00"}),
            "resistencia_min": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Ex: 130", "data-original": ""}),
            "resistencia_max": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Ex: 160", "data-original": ""}),

            "dureza": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "placeholder": "Ex: 80"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        for field in self.Meta.fields:
            if cleaned_data.get(field) == "":
                cleaned_data[field] = None
        return cleaned_data


# ---------------------------------------------------------
# 4) FormSets
# ---------------------------------------------------------
fields_composicao = [
    "tipo_abnt", "c_min", "c_max", "mn_min", "mn_max",
    "si_min", "si_max", "p_min", "p_max", "s_min", "s_max",
    "cr_min", "cr_max", "ni_min", "ni_max", "cu_min", "cu_max",
    "al_min", "al_max",
]

ComposicaoFormSet = forms.modelformset_factory(
    NormaComposicaoElemento,
    form=ComposicaoQuimicaForm,
    extra=1,
    can_delete=True,
    fields=fields_composicao,
    formset=BaseEmptyModelFormSet,
)

fields_tracao = [
    "tipo_abnt",
    "bitola_minima", "bitola_maxima",
    "resistencia_min", "resistencia_max",
    "dureza",
]

TracaoFormSet = forms.modelformset_factory(
    NormaTracao,
    form=TracaoForm,
    extra=1,
    can_delete=True,
    fields=fields_tracao,
    formset=BaseEmptyModelFormSet,
)
