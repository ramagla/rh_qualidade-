from datetime import datetime

from django import forms
from django_select2.forms import Select2Widget

from Funcionario.models import Funcionario
from metrologia.models import Afericao, CalibracaoDispositivo, TabelaTecnica
from django.core.files.uploadedfile import UploadedFile


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
            "anexo": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.calibracao_cliente:
                    # 🔒 Mantém apenas os campos essenciais
                    manter = ["codigo_dispositivo", "data_afericao", "observacoes", "anexo"]
                    for campo in list(self.fields.keys()):
                        if campo not in manter:
                            self.fields.pop(campo)
                            
        # Converter data do banco para o formato YYYY-MM-DD (necessário para o input type="date")
        if self.instance and self.instance.data_afericao:
            self.initial["data_afericao"] = self.instance.data_afericao

        # Carregar dados dinâmicos e ordenar
# Sinalização do modo "calibração do cliente"
        is_cliente = False
        if "calibracao_cliente" in self.data:
            val = self.data.get("calibracao_cliente")
            is_cliente = str(val).lower() in ("1", "true", "on")
        elif getattr(self.instance, "calibracao_cliente", False):
            is_cliente = True

        self.fields["instrumento_utilizado"] = forms.ModelChoiceField(
            queryset=TabelaTecnica.objects.all().order_by("nome_equipamento"),
            widget=Select2Widget(attrs={"class": "form-select"}),
            empty_label="Selecione um instrumento",
            label="Instrumento",
            required=not is_cliente,
        )
        self.fields["nome_responsavel"] = forms.ModelChoiceField(
            queryset=Funcionario.objects.all().order_by("nome"),
            widget=Select2Widget(attrs={"class": "form-select"}),
            empty_label="Selecione um responsável",
            label="Nome do Responsável",
            required=not is_cliente,
        )
    def clean_anexo(self):
            f = self.cleaned_data.get("anexo")
            if isinstance(f, UploadedFile) and f.size > 5 * 1024 * 1024:
                raise forms.ValidationError("O arquivo excede 5 MB.")
            return f
    
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
