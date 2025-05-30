from django import forms

from ..models.matriz_polivalencia import Atividade, MatrizPolivalencia, Nota
from django_select2.forms import Select2Widget  # se estiver usando Select2
from django.forms import TypedChoiceField
from Funcionario.models.departamentos import Departamentos
from rh_qualidade.utils import formatar_nome_atividade_com_siglas



from django import forms
from django_select2.forms import Select2Widget
from ..models.matriz_polivalencia import MatrizPolivalencia


class MatrizPolivalenciaForm(forms.ModelForm):
    class Meta:
        model = MatrizPolivalencia
        fields = "__all__"
        widgets = {
            "elaboracao": Select2Widget(attrs={"class": "form-select select2"}),
            "coordenacao": Select2Widget(attrs={"class": "form-select select2"}),
            "validacao": Select2Widget(attrs={"class": "form-select select2"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplica manualmente o id="departamento" para o JS funcionar corretamente
        self.fields["departamento"].widget.attrs.update({
            "class": "form-select select2",
            "id": "departamento"
        })

        # Torna todos os campos opcionais
        for name, field in self.fields.items():
            field.required = False



class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = "__all__"
        widgets = {
            "departamentos": forms.SelectMultiple(attrs={"class": "form-select select2", "multiple": "multiple"})
        }

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome:
            return formatar_nome_atividade_com_siglas(nome)
        return nome


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = "__all__"
