from django import forms
from Funcionario.models.banco_horas import BancoHoras

class BancoHorasForm(forms.ModelForm):
    he_50 = forms.BooleanField(required=False)
    he_100 = forms.BooleanField(required=False)

    observacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Digite observações relevantes"
        })
    )

    saldo_horas = forms.DecimalField(
        label="Saldo (h)",
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "class": "form-control"})
    )

    class Meta:
        model = BancoHoras
        fields = ['funcionario', 'data', 'horas_trabalhadas', 'observacao', 'he_50', 'he_100', 'ocorrencia']

        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select select2'}),
            'data': forms.DateInput(format="%Y-%m-%d", attrs={'type': 'date', 'class': 'form-control'}),
            'horas_trabalhadas': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 01:30 ou -01:30'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["funcionario"].queryset = self.fields["funcionario"].queryset.order_by("nome")

        # Corrigir exibição inicial de horas_trabalhadas (±HH:MM)
        if self.instance and self.instance.horas_trabalhadas is not None:
            duracao = self.instance.horas_trabalhadas
            total_minutos = int(duracao.total_seconds() // 60)

            sinal = "-" if total_minutos < 0 else ""
            total_minutos = abs(total_minutos)
            horas = total_minutos // 60
            minutos = total_minutos % 60

            self.initial["horas_trabalhadas"] = f"{sinal}{horas:02}:{minutos:02}"
