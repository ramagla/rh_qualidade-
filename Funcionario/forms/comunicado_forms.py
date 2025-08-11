from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from rh_qualidade.utils import title_case
from ..models import Comunicado


class ComunicadoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de Comunicados.
    Usa CKEditor para o conteúdo do comunicado e widgets Bootstrap para os demais campos.
    Aplica title_case em assunto e departamento responsável.
    """

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
        label="Lista de Assinaturas"
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
        """
        Aplica title_case ao assunto do comunicado.
        """
        assunto = self.cleaned_data.get("assunto", "")
        return title_case(assunto) if assunto else assunto
    
    def clean_lista_assinaturas(self):
        f = self.cleaned_data.get("lista_assinaturas")
        if f and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("O arquivo excede 5 MB.")
        return f

    def clean_departamento_responsavel(self):
        """
        Aplica title_case ao campo departamento_responsavel.
        """
        departamento = self.cleaned_data.get("departamento_responsavel", "")
        return title_case(departamento) if departamento else departamento
