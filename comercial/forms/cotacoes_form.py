from django import forms
from comercial.models import Cotacao

class CotacaoForm(forms.ModelForm):
    class Meta:
        model = Cotacao
        fields = ['titulo', 'observacoes']
