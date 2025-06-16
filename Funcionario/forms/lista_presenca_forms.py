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
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
            ),
            "data_fim": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
                format="%Y-%m-%d"
            ),
            "participantes": forms.SelectMultiple(attrs={"class": "form-select"}),
            "horario_inicio": forms.TimeInput(
                attrs={"type": "time", "class": "form-control d-none"},
                format="%H:%M"
            ),
            "horario_fim": forms.TimeInput(
                attrs={"type": "time", "class": "form-control d-none"},
                format="%H:%M"
            ),
            "duracao": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.25", "min": "0"}
            ),
            "instrutor": forms.TextInput(attrs={"class": "form-control"}),
            "assunto": forms.TextInput(attrs={"class": "form-control"}),
            "situacao": forms.Select(attrs={"class": "form-select"}),
            "planejado": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Oculta os campos de hora (mesmo carregando valor se existir)
        self.fields["horario_inicio"].widget = forms.HiddenInput()
        self.fields["horario_fim"].widget = forms.HiddenInput()

        # Garante o formato correto das datas
        for field in ["data_inicio", "data_fim"]:
            if self.instance and getattr(self.instance, field):
                self.initial[field] = getattr(self.instance, field).strftime("%Y-%m-%d")

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")

        if not data_inicio:
            raise ValidationError(
                {"data_inicio": 'O campo "Data de Início" é obrigatório.'}
            )

        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValidationError("A data de fim não pode ser anterior à data de início.")

        return cleaned_data
