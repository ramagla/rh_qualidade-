from django import forms
from Funcionario.models.banco_horas import BancoHoras

class BancoHorasForm(forms.ModelForm):
    """
    Formulário para registro e edição do Banco de Horas.
    Aplica widgets customizados e formatação especial para campo de horas trabalhadas.
    """
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

    class Meta:
        model = BancoHoras
        fields = [
            'funcionario',
            'data',
            'horas_trabalhadas',
            'observacao',
            'he_50',
            'he_100',
            'ocorrencia'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={
                'class': 'form-select select2'
            }),
            'data': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'horas_trabalhadas': forms.TextInput(attrs={
                'placeholder': 'Ex: 01:30 ou -01:30',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordena funcionários por nome no select
        self.fields["funcionario"].queryset = self.fields["funcionario"].queryset.order_by("nome")
        # Campos obrigatórios
        self.fields["data"].required = True
        self.fields["horas_trabalhadas"].required = True
        # Exibe horas trabalhadas já formatadas, se houver instância
        if self.instance and self.instance.horas_trabalhadas is not None:
            duracao = self.instance.horas_trabalhadas
            total_minutos = int(duracao.total_seconds() // 60)
            sinal = "-" if total_minutos < 0 else ""
            total_minutos = abs(total_minutos)
            horas = total_minutos // 60
            minutos = total_minutos % 60
            self.initial["horas_trabalhadas"] = f"{sinal}{horas:02}:{minutos:02}"

