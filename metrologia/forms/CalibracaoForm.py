from django import forms

from metrologia.models.models_calibracao import Calibracao


class CalibracaoForm(forms.ModelForm):
    # Campo de exatidão requerida (somente leitura)
    exatidao_requerida = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        label="Exatidão Requerida (ER = TP/2)",
        widget=forms.TextInput(attrs={"readonly": "readonly", "class": "form-control"}),
    )

    # Campo de data com seleção de calendário
    data_calibracao = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data da Calibração",
    )

    class Meta:
        model = Calibracao
        fields = [
            "codigo",
            "laboratorio",
            "numero_certificado",
            "erro_equipamento",
            "incerteza",
            "data_calibracao",
            "certificado_anexo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Preenche o campo Exatidão Requerida com base no equipamento selecionado
        if self.instance and hasattr(self.instance, "codigo") and self.instance.codigo:
            self.fields["exatidao_requerida"].initial = (
                self.instance.codigo.exatidao_requerida
            )
        else:
            self.fields["exatidao_requerida"].initial = None

        # Configurações para exibir corretamente o campo de código com um select (se aplicável)
        self.fields["codigo"].widget.attrs.update(
            {
                "class": "form-select select2",
            }
        )

        # Configurações para o campo de laboratório (seja select ou text input)
        self.fields["laboratorio"].widget.attrs.update(
            {
                "class": "form-select select2",
            }
        )

        # Adicionar classe bootstrap nos outros campos
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs.update({"class": "form-control"})
