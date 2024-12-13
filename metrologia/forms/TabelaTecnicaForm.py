from django import forms
from ..models.models_tabelatecnica import TabelaTecnica

class TabelaTecnicaForm(forms.ModelForm):
    class Meta:
        model = TabelaTecnica
        fields = '__all__'  # Inclui todos os campos do modelo

    def __init__(self, *args, **kwargs):
        super(TabelaTecnicaForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
