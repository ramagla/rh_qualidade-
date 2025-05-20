from django import forms

from ..models.matriz_polivalencia import Atividade, MatrizPolivalencia, Nota
from ..models.choices_departamento import DEPARTAMENTOS_EMPRESA
from django_select2.forms import Select2Widget  # se estiver usando Select2


class MatrizPolivalenciaForm(forms.ModelForm):
    class Meta:
        model = MatrizPolivalencia
        fields = "__all__"
        widgets = {
            "departamento": Select2Widget(attrs={"class": "form-select", "data-placeholder": "Selecione um departamento"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False



class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = "__all__"

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome:
            return nome.title()  # Aplica Title Case apenas no campo nome
        return nome


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"
