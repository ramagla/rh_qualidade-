from django import forms
from portaria.models.ocorrencia import OcorrenciaPortaria
from Funcionario.models import Funcionario
from django_select2.forms import Select2MultipleWidget
from django_ckeditor_5.widgets import CKEditor5Widget

class OcorrenciaPortariaForm(forms.ModelForm):
    class Meta:
        model = OcorrenciaPortaria
        exclude = ["responsavel_registro"]  # <- aqui removemos do formulário
        widgets = {
            "descricao": CKEditor5Widget(),
            "pessoas_envolvidas": Select2MultipleWidget,
            "data_inicio": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "data_fim": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}),
        }
