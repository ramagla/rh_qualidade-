from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from rh_qualidade.utils import title_case

from ..models import Treinamento


class TreinamentoForm(forms.ModelForm):
    descricao = forms.CharField(
        widget=CKEditor5Widget(config_name="default"),
        required=False,  # Torna o campo opcional
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
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        situacao = cleaned_data.get("situacao")

        # Validar que situação está preenchida apenas se o status for 'requerido'
        if status == "requerido" and not situacao:
            raise forms.ValidationError(
                {"situacao": 'A situação é obrigatória quando o status é "Requerido".'}
            )
        return cleaned_data

    def clean_nome_curso(self):
        nome_curso = self.cleaned_data.get("nome_curso")
        if nome_curso:
            return title_case(nome_curso)  # Aplica a função title_case personalizada
        return nome_curso

    def clean_instituicao_ensino(self):
        instituicao_ensino = self.cleaned_data.get("instituicao_ensino")
        if instituicao_ensino:
            # Aplica a função title_case personalizada
            return title_case(instituicao_ensino)
        return instituicao_ensino
