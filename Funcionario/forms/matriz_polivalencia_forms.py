from django import forms
from ..models.matriz_polivalencia import MatrizPolivalencia, Atividade, Nota

class MatrizPolivalenciaForm(forms.ModelForm):
    class Meta:
        model = MatrizPolivalencia
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna todos os campos opcionais
        for field in self.fields.values():
            field.required = False

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = '__all__'


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = '__all__'
