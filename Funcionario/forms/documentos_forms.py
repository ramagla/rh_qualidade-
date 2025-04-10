from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django_select2.forms import Select2Widget

from Funcionario.models import Documento, RevisaoDoc
from rh_qualidade.utils import title_case


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ["nome", "codigo", "arquivo", "responsavel_recuperacao", "status"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "arquivo": forms.FileInput(attrs={"class": "form-control"}),
            # Select2 aplicado
            "responsavel_recuperacao": Select2Widget(
                attrs={"class": "select2 form-select"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome:
            return title_case(nome)  # Aplica a função title_case personalizada
        return nome


class RevisaoDocForm(forms.ModelForm):
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = RevisaoDoc
        fields = ["numero_revisao", "data_revisao", "descricao_mudanca"]
        widgets = {
            "numero_revisao": forms.TextInput(attrs={"class": "form-control"}),
            "data_revisao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            # Corrige esta linha
            "descricao_mudanca": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
        }
