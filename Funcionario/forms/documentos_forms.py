from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from django_select2.forms import Select2Widget

from Funcionario.models import Documento, RevisaoDoc


from Funcionario.models.departamentos import Departamentos

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = [
            "nome", "codigo", "arquivo", "responsavel_recuperacao", "status",
            "coleta", "recuperacao", "arquivo_tipo", "local_armazenamento",
            "tempo_retencao", "descarte", "departamentos"
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "arquivo": forms.FileInput(attrs={"class": "form-control"}),
            "responsavel_recuperacao": Select2Widget(attrs={"class": "select2 form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "departamentos": forms.SelectMultiple(attrs={"class": "form-select select2"}),
            "coleta": forms.TextInput(attrs={"class": "form-control"}),
            "recuperacao": forms.TextInput(attrs={"class": "form-control"}),
            "arquivo_tipo": forms.Select(attrs={"class": "form-select"}),
            "local_armazenamento": forms.TextInput(attrs={"class": "form-control"}),
            "tempo_retencao": forms.TextInput(attrs={"class": "form-control"}),
            "descarte": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["departamentos"].queryset = Departamentos.objects.all().order_by("nome")



class RevisaoDocForm(forms.ModelForm):
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = RevisaoDoc
        fields = ["numero_revisao", "data_revisao", "descricao_mudanca"]
        widgets = {
            "numero_revisao": forms.TextInput(attrs={"class": "form-control"}),
            "data_revisao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "descricao_mudanca": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
