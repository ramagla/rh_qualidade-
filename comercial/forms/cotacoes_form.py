# comercial/forms/cotacao_forms.py

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from comercial.models import Cotacao, Cliente
from django.contrib.auth import get_user_model

User = get_user_model()


class CotacaoForm(forms.ModelForm):
    """
    Formulário de Cotação.
    'data_abertura' e 'responsavel' são definidos em view (não expostos ao usuário).
    """
    class Meta:
        model = Cotacao
        # excluímos data_abertura e responsavel aqui — serão atribuídos em view
        fields = [
            "tipo",
            "cliente",
            "frete",
            "cond_pagamento",
            "icms",
            "observacoes",
        ]
        widgets = {
            "tipo": forms.Select(
                attrs={"class": "form-select select2"},
            ),
            "cliente": forms.Select(
                attrs={"class": "form-select select2"},
            ),
            "frete": forms.Select(
                attrs={"class": "form-select select2"},
            ),
            "cond_pagamento": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Condição de pagamento"},
            ),
            "icms": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "ICMS (%)"},
            ),
            "observacoes": CKEditor5Widget(
                config_name="default",
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Recebe opcionalmente 'user' para já vincular ao campo responsavel.
        """
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # garante que o campo cliente tenha queryset atualizado, se precisar filtrar:
        self.fields["cliente"].queryset = Cliente.objects.filter(tipo_cadastro="Cliente").order_by("razao_social")

        if user:
            # instancia já com o responsável definido
            self.instance.responsavel = user
