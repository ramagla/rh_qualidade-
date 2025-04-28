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
        if "id" in form.fields:
            del form.fields["id"]
        if i >= self.initial_form_count():
            form.empty_permitted = True
        return form


# ---------------------------------------------------------
# 1) Cabeçalho da Norma
# ---------------------------------------------------------
class NormaTecnicaForm(forms.ModelForm):
    nome_norma = forms.ChoiceField(
        label="Nome da Norma",
        choices=[],
        widget=forms.Select(attrs={"class": "form-select select2"}),
    )

    vinculo_norma = forms.ChoiceField(
        label="Norma vinculada (tração)",
        choices=[("", "— Selecione —")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select select2"}),
    )

    class Meta:
        model = NormaTecnica
        fields = ["nome_norma", "arquivo_norma", "vinculo_norma"]
        widgets = {
            "arquivo_norma": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        normas_catalogo = (
            MateriaPrimaCatalogo.objects.exclude(norma__isnull=True)
            .exclude(norma="")
            .values_list("norma", flat=True)
            .distinct()
            .order_by("norma")
        )
        choices = [("", "— Selecione —")] + [(n, n) for n in normas_catalogo]
        self.fields["nome_norma"].choices = choices
        self.fields["vinculo_norma"].choices = choices

    def clean_vinculo_norma(self):
        return self.cleaned_data.get("vinculo_norma")


# ---------------------------------------------------------
# 2) Composição Química
# ---------------------------------------------------------
class ComposicaoQuimicaForm(forms.ModelForm):
    tipo_abnt = forms.ChoiceField(
        label="Tipo de Aço ABNT",
        choices=[],
        widget=forms.Select(attrs={"class": "form-select select2"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "id" in self.fields:
            del self.fields["id"]
        tipos = (
            MateriaPrimaCatalogo.objects.exclude(tipo_abnt__isnull=True)
            .exclude(tipo_abnt="")
            .values_list("tipo_abnt", flat=True)
            .distinct()
            .order_by("tipo_abnt")
        )
        self.fields["tipo_abnt"].choices = [("", "—")] + [(t, t) for t in tipos]
        for fld in self.Meta.element_fields:
            self.fields[fld].required = False
            self.fields[fld].widget.attrs.update(
                {"class": "form-control", "step": "0.001"}
            )

    def clean(self):
        cleaned_data = super().clean()
        for fld in self.Meta.element_fields:
            if cleaned_data.get(fld) == "":
                cleaned_data[fld] = None
        return cleaned_data

    class Meta:
        model = NormaComposicaoElemento
        element_fields = [
            "c_min",
            "c_max",
            "mn_min",
            "mn_max",
            "si_min",
            "si_max",
            "p_min",
            "p_max",
            "s_min",
            "s_max",
            "cr_min",
            "cr_max",
            "ni_min",
            "ni_max",
            "cu_min",
            "cu_max",
            "al_min",
            "al_max",
        ]
        fields = ["tipo_abnt", *element_fields]


# ---------------------------------------------------------
# 3) Faixa de Resistência à Tração
# ---------------------------------------------------------
class TracaoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].required = False
            self.fields[field].widget.attrs.update({"class": "form-control"})
        self.fields["dureza"].widget.attrs.update({"placeholder": "Ex: HRb 80"})

    def clean(self):
        cleaned_data = super().clean()
        for field in self.Meta.fields:
            if cleaned_data.get(field) == "":
                cleaned_data[field] = None
        return cleaned_data

    class Meta:
        model = NormaTracao
        fields = [
            "bitola_minima",
            "bitola_maxima",
            "resistencia_min",
            "resistencia_max",
            "dureza",
        ]
        widgets = {
            "bitola_minima": forms.NumberInput(attrs={"step": "0.01"}),
            "bitola_maxima": forms.NumberInput(attrs={"step": "0.01"}),
            "resistencia_min": forms.NumberInput(attrs={"step": "0.01"}),
            "resistencia_max": forms.NumberInput(attrs={"step": "0.01"}),
            "dureza": forms.NumberInput(
                attrs={"step": "0.01", "class": "form-control"}
            ),
        }


# ---------------------------------------------------------
# 4) FormSets
# ---------------------------------------------------------
fields_composicao = [
    "tipo_abnt",
    "c_min",
    "c_max",
    "mn_min",
    "mn_max",
    "si_min",
    "si_max",
    "p_min",
    "p_max",
    "s_min",
    "s_max",
    "cr_min",
    "cr_max",
    "ni_min",
    "ni_max",
    "cu_min",
    "cu_max",
    "al_min",
    "al_max",
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
    "bitola_minima",
    "bitola_maxima",
    "resistencia_min",
    "resistencia_max",
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
