from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from rh_qualidade.utils import title_case
from ..models import Treinamento

class TreinamentoForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de treinamentos.
    Usa CKEditor para descrição, widgets customizados e valida situação e campos textuais.
    """
    descricao = forms.CharField(
        widget=CKEditor5Widget(config_name="default"),
        required=False,
    )

    class Meta:
        model = Treinamento
        fields = "__all__"
        widgets = {
            "funcionario": forms.Select(attrs={"class": "form-select"}),
            "tipo": forms.Select(
                choices=Treinamento.TIPO_TREINAMENTO_CHOICES,
                attrs={"class": "form-select"},
            ),
            "categoria": forms.Select(
                choices=Treinamento.CATEGORIA_CHOICES, attrs={"class": "form-select"}
            ),
            "nome_curso": forms.TextInput(attrs={"class": "form-control"}),
            "instituicao_ensino": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(
                choices=Treinamento.STATUS_CHOICES, attrs={"class": "form-select"}
            ),
            "data_inicio": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_fim": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "carga_horaria": forms.TextInput(attrs={"class": "form-control"}),
            "anexo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "situacao": forms.Select(
                choices=Treinamento.SITUACAO_CHOICES, attrs={"class": "form-select"}
            ),
            "necessita_avaliacao": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        situacao = cleaned_data.get("situacao")

        # Validar que situação está preenchida apenas se o status for 'requerido'
        if status == "requerido" and not situacao:
            self.add_error("situacao", 'A situação é obrigatória quando o status é "Requerido".')
        return cleaned_data

    def clean_nome_curso(self):
        nome_curso = self.cleaned_data.get("nome_curso")
        if nome_curso:
            return title_case(nome_curso)
        return nome_curso

    def clean_instituicao_ensino(self):
        instituicao_ensino = self.cleaned_data.get("instituicao_ensino")
        if instituicao_ensino:
            return title_case(instituicao_ensino)
        return instituicao_ensino

    def clean_necessita_avaliacao(self):
        valor = self.cleaned_data.get("necessita_avaliacao")
        if isinstance(valor, str):
            return valor == "True"
        return bool(valor)
