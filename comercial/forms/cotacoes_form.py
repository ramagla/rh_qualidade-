# comercial/forms/cotacao_forms.py

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from comercial.models import Cotacao, Cliente
from django.contrib.auth import get_user_model

User = get_user_model()


# comercial/forms/cotacao_forms.py

class CotacaoForm(forms.ModelForm):
    class Meta:
        model = Cotacao
        fields = ["tipo", "cliente", "frete", "cond_pagamento", "icms", "validade_proposta", "observacoes"]


        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select select2"}),
            "cliente": forms.Select(attrs={"class": "form-select select2"}),
            "frete": forms.Select(attrs={"class": "form-select select2"}),
            "cond_pagamento": forms.TextInput(attrs={"class": "form-control", "placeholder": "Condição de pagamento"}),
            "icms": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "ICMS (%)"}),
            "observacoes": CKEditor5Widget(config_name="default"),
            "validade_proposta": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Validade da proposta (em dias)",
                "min": "1"
            }),

        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["cliente"].queryset = Cliente.objects.filter(tipo_cadastro="Cliente").order_by("razao_social")

        self.user = user  # guarda para uso posterior

        if not self.instance.pk:
            self.fields["observacoes"].initial = (
                "As especificações gerais de fabricações (Normas tolerâncias e desenho definitivo), "
                "serão analisados e definidos em conjuntos pelas engenharias da BRAS-MOL e do cliente antes do início do desenvolvimento.\n\n"
                "Considerar-se-á pedido satisfeito, aquele cuja quantidade entregue for 10% inferior ou 10% superior à solicitada.\n\n"
                "Não previsto custo de projeto ferramental, sendo este de propriedade da BRAS-MOL."
            )

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Força o responsável caso o campo não venha no POST (como hidden)
        if not instance.responsavel_id and self.user:
            instance.responsavel = self.user

        if commit:
            instance.save()
        return instance


