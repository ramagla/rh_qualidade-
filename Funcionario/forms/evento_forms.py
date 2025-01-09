from django import forms
from ..models import Evento

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'cor', 'tipo']

    # Configurando widgets para data sem horário
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Define o tipo como 'date' para não incluir hora
            'class': 'form-control',
        }),
        label="Data de Início"
    )
    
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',  # Define o tipo como 'date' para não incluir hora
            'class': 'form-control',
        }),
        label="Data de Fim"
    )