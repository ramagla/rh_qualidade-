from django import forms
from ..models import ListaPresenca
from django_ckeditor_5.widgets import CKEditor5Widget


class ListaPresencaForm(forms.ModelForm):
    descricao = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = ListaPresenca
        fields = '__all__'
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'participantes': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duracao': forms.TextInput(attrs={'class': 'form-control'}),
            'instrutor': forms.TextInput(attrs={'class': 'form-control'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control'}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_instrutor(self):
        instrutor = self.cleaned_data.get('instrutor')
        if instrutor:
            return instrutor.title()  # Converte para Title Case
        return instrutor

    def clean_assunto(self):
        assunto = self.cleaned_data.get('assunto')
        if assunto:
            return assunto.title()  # Converte para Title Case
        return assunto

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError("A data de fim não pode ser anterior à data de início.")

        return cleaned_data
