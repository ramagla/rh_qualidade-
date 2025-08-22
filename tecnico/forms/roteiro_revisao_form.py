# tecnico/forms/roteiro_revisao_form.py
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from tecnico.models.roteiro import RoteiroRevisao

class RoteiroRevisaoForm(forms.ModelForm):
    descricao_mudanca = forms.CharField(widget=CKEditor5Widget(), required=False)

    class Meta:
        model = RoteiroRevisao
        fields = ["numero_revisao", "data_revisao", "descricao_mudanca", "status"]
        widgets = {
            "numero_revisao": forms.TextInput(attrs={"class": "form-control"}),
            "data_revisao": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
