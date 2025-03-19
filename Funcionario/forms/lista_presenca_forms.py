from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from ..models import ListaPresenca


class ListaPresencaForm(forms.ModelForm):
    descricao = forms.CharField(widget=CKEditor5Widget(config_name="default"))

    class Meta:
        model = ListaPresenca
        fields = "__all__"
        widgets = {
            "data_inicio": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_fim": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "participantes": forms.SelectMultiple(attrs={"class": "form-select"}),
            "horario_inicio": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "horario_fim": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "duracao": forms.NumberInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "instrutor": forms.TextInput(attrs={"class": "form-control"}),
            "assunto": forms.TextInput(attrs={"class": "form-control"}),
            "situacao": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        horario_inicio = cleaned_data.get("horario_inicio")
        horario_fim = cleaned_data.get("horario_fim")

        # Validação de datas
        if not data_inicio:
            raise ValidationError(
                {"data_inicio": 'O campo "Data de Início" é obrigatório.'}
            )

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError(
                "A data de fim não pode ser anterior à data de início."
            )

        return cleaned_data
