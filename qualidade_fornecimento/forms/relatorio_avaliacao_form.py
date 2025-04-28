# forms/relatorio_avaliacao_form.py
from django import forms

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado

SEMESTRES = [
    ("1", "1º Semestre"),
    ("2", "2º Semestre"),
]


class RelatorioAvaliacaoForm(forms.Form):
    ano = forms.IntegerField(
        label="Ano",
        initial=2024,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    semestre = forms.ChoiceField(
        choices=SEMESTRES, widget=forms.Select(attrs={"class": "form-select"})
    )
    fornecedor = forms.ModelChoiceField(
        queryset=FornecedorQualificado.objects.all(),
        widget=forms.Select(attrs={"class": "form-select select2"}),
        label="Fornecedor",
    )
    tipo = forms.ChoiceField(
        choices=[("material", "Material"), ("servico", "Serviço Externo")],
        widget=forms.RadioSelect,
        initial="material",
        label="Tipo de Fornecimento",
    )
