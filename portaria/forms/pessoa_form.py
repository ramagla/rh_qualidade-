# portaria/forms.py
from django import forms
from portaria.models import PessoaPortaria

class PessoaPortariaForm(forms.ModelForm):
    class Meta:
        model = PessoaPortaria
        fields = ['nome', 'tipo', 'documento', 'empresa', 'foto', 'veiculos_vinculados']
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select select2", "id": "id_tipo"}),
            "nome": forms.TextInput(attrs={"class": "form-control", "id": "id_nome"}),
            "documento": forms.TextInput(attrs={"class": "form-control", "id": "id_documento", "placeholder": "Ex: 12.345.678-9"}),
            "empresa": forms.TextInput(attrs={"class": "form-control"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control", "id": "id_foto", "accept": "image/*", "capture": "user"}),
            'veiculos_vinculados': forms.SelectMultiple(attrs={"class": "form-select select2 w-100"}),

        }
