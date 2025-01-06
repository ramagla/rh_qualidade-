from django import forms
from metrologia.models import CalibracaoDispositivo, TabelaTecnica
from Funcionario.models import Funcionario
from django_select2.forms import Select2Widget

class CalibracaoDispositivoForm(forms.ModelForm):
    class Meta:
        model = CalibracaoDispositivo
        fields = [
            'codigo_dispositivo',
            'instrumento_medicao',
            'afericao',
            'status',
            'instrumento_utilizado',
            'data_afericao',
            'nome_responsavel',
            'observacoes',
        ]
        widgets = {
            'codigo_dispositivo': Select2Widget(attrs={'class': 'form-select'}),
            'instrumento_utilizado': Select2Widget(attrs={'class': 'form-select'}),
            'nome_responsavel': Select2Widget(attrs={'class': 'form-select'}),
            'data_afericao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Carregar dados dinâmicos e ordenar
        self.fields['instrumento_medicao'] = forms.ModelChoiceField(
            queryset=TabelaTecnica.objects.all().order_by('nome_equipamento'),
            widget=Select2Widget(attrs={'class': 'form-select'}),
            empty_label="Selecione um instrumento",
            label="Instrumento de Medição"
        )
        self.fields['nome_responsavel'] = forms.ModelChoiceField(
            queryset=Funcionario.objects.all().order_by('nome'),
            widget=Select2Widget(attrs={'class': 'form-select'}),
            empty_label="Selecione um responsável",
            label="Nome do Responsável"
        )

    def clean_afericao(self):
        """Converte vírgulas para pontos no campo afericao."""
        afericao = self.cleaned_data.get('afericao')
        if afericao and isinstance(afericao, str):
            try:
                # Substitui vírgula por ponto e converte para decimal
                afericao = afericao.replace(',', '.')
                return float(afericao)  # Ou Decimal, caso necessário
            except ValueError:
                raise forms.ValidationError("Insira um valor numérico válido.")
        return afericao
