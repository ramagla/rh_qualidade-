from django import forms
from django_select2.forms import Select2Widget

from ..models.matriz_polivalencia import Atividade, MatrizPolivalencia, Nota
from rh_qualidade.utils import formatar_nome_atividade_com_siglas

class MatrizPolivalenciaForm(forms.ModelForm):
    """
    Formulário para cadastro/edição de Matriz de Polivalência.
    Usa Select2 nos campos-chave e deixa todos os campos opcionais para flexibilizar o preenchimento.
    """
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
    """
    Formulário para cadastro/edição de Atividade.
    Usa Select2 em departamentos e formata o nome da atividade com siglas personalizadas.
    """
    class Meta:
        model = Atividade
        fields = "__all__"
        widgets = {
            "departamentos": forms.SelectMultiple(
                attrs={"class": "form-select select2", "multiple": "multiple"}
            )
        }

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome:
            return formatar_nome_atividade_com_siglas(nome)
        return nome

class NotaForm(forms.ModelForm):
    """
    Formulário para cadastro/edição de Notas de Polivalência.
    """
    class Meta:
        model = Nota
        fields = "__all__"
