from django import forms
from django.forms.widgets import Textarea

from rh_qualidade.utils import title_case

from ..models import Comunicado


class ComunicadoForm(forms.ModelForm):
    descricao = forms.CharField(widget=Textarea(attrs={
        'class': 'form-control tinymce',
        'readonly': False,  # redundante, mas previne sobrescrita
        'disabled': False,
    }))

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
            "departamento_responsavel": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "lista_assinaturas": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_assunto(self):
        assunto = self.cleaned_data.get("assunto")
        if assunto:
            return title_case(assunto)  # Aplica a função title_case personalizada
        return assunto

    def clean_departamento_responsavel(self):
        departamento_responsavel = self.cleaned_data.get("departamento_responsavel")
        if departamento_responsavel:
            # Aplica a função title_case personalizada
            return title_case(departamento_responsavel)
        return departamento_responsavel
