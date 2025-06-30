from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from rh_qualidade.utils import title_case
from ..models import Comunicado


class ComunicadoForm(forms.ModelForm):
    descricao = forms.CharField(
        widget=CKEditor5Widget(
            config_name="default",
            attrs={"placeholder": "Digite o conteúdo do comunicado"}
        ),
        required=True
    )

    lista_assinaturas = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Comunicado
        fields = [
            "data",
            "assunto",
            "descricao",
            "tipo",
            "departamento_responsavel",
            "lista_assinaturas",
        ]

        widgets = {
            "data": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "assunto": forms.TextInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "departamento_responsavel": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_assunto(self):
        assunto = self.cleaned_data.get("assunto", "")
        return title_case(assunto) if assunto else assunto

    def clean_departamento_responsavel(self):
        departamento = self.cleaned_data.get("departamento_responsavel", "")
        return title_case(departamento) if departamento else departamento
