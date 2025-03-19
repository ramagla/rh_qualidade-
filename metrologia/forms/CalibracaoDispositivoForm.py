from datetime import datetime

from django import forms
from django_select2.forms import Select2Widget

from Funcionario.models import Funcionario
from metrologia.models import Afericao, CalibracaoDispositivo, TabelaTecnica


class CalibracaoDispositivoForm(forms.ModelForm):
    class Meta:
        model = CalibracaoDispositivo
        fields = "__all__"

        widgets = {
            "codigo_dispositivo": Select2Widget(attrs={"class": "form-select"}),
            "instrumento_utilizado": Select2Widget(attrs={"class": "form-select"}),
            "nome_responsavel": Select2Widget(attrs={"class": "form-select"}),
            "data_afericao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"
            ),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Converter data do banco para o formato YYYY-MM-DD (necessário para o input type="date")
        if self.instance and self.instance.data_afericao:
            self.initial["data_afericao"] = self.instance.data_afericao

        # Carregar dados dinâmicos e ordenar
        self.fields["instrumento_utilizado"] = forms.ModelChoiceField(
            queryset=TabelaTecnica.objects.all().order_by("nome_equipamento"),
            widget=Select2Widget(attrs={"class": "form-select"}),
            empty_label="Selecione um instrumento",
            label="Instrumento",
        )
        self.fields["nome_responsavel"] = forms.ModelChoiceField(
            queryset=Funcionario.objects.all().order_by("nome"),
            widget=Select2Widget(attrs={"class": "form-select"}),
            empty_label="Selecione um responsável",
            label="Nome do Responsável",
        )

    def clean_data_afericao(self):
        data = self.cleaned_data.get("data_afericao")
        if isinstance(data, str):
            try:
                data = datetime.strptime(data, "%Y-%m-%d").date()
            except ValueError:
                raise forms.ValidationError("Data inválida. Use o formato YYYY-MM-DD.")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()  # Garante que a instância tenha uma `primary key`
        return instance


class AfericaoForm(forms.ModelForm):
    class Meta:
        model = Afericao
        fields = ["cota", "valor"]
