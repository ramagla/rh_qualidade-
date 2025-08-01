from django import forms
from metrologia.models import AnaliseCriticaMetrologia

class AnaliseCriticaMetrologiaForm(forms.ModelForm):
    class Meta:
        model = AnaliseCriticaMetrologia
        fields = [
            "equipamento_instrumento",
            "equipamento_dispositivo",
            "descricao_equipamento",
            "modelo",
            "capacidade_medicao",
            "data_ultima_calibracao",
            "nao_conformidade_detectada",
            "compromete_qualidade",
            "observacoes_qualidade",
            "verificar_pecas_processo",
            "observacoes_pecas",
            "comunicar_cliente",
            "observacoes_cliente",
            "tipo",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "equipamento_instrumento": forms.Select(attrs={"class": "form-select select2", "data-placeholder": "Selecione o instrumento..."}),
            "equipamento_dispositivo": forms.Select(attrs={"class": "form-select select2", "data-placeholder": "Selecione o dispositivo..."}),

            "descricao_equipamento": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "modelo": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "capacidade_medicao": forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
            "data_ultima_calibracao": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "readonly": "readonly", "type": "date"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Oculta os campos de observação por padrão (JS ativará quando booleanos forem True)
        self.fields["observacoes_qualidade"].required = False
        self.fields["observacoes_pecas"].required = False
        self.fields["observacoes_cliente"].required = False
