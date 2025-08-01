from django import forms
from qualidade_fornecimento.models.inspecao10 import Inspecao10
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from django_ckeditor_5.widgets import CKEditor5Widget
from django.utils.timezone import now
from datetime import date
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from Funcionario.models.departamentos import Departamentos


class Inspecao10Form(forms.ModelForm):
    class Meta:
        model = Inspecao10
        fields = [
            "numero_op", "codigo_brasmol", "data", "fornecedor", "hora_inicio",
            "hora_fim", "quantidade_total", "quantidade_nok", "disposicao", "observacoes","setor",
        ]



        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "hora_fim": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "fornecedor": forms.Select(attrs={
                    "class": "form-select select2"
                }),
            "codigo_brasmol": forms.Select(attrs={"class": "form-select select2"}),
            "disposicao": forms.Select(attrs={"class": "form-select"}),
            "setor": forms.Select(attrs={"class": "form-select select2"}),


            "observacoes": CKEditor5Widget(
                config_name="default",
                attrs={"placeholder": "Digite a observação sobre a falha de banho"}
            ),
        }

    from django.utils.timezone import now

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fornecedor"].queryset = FornecedorQualificado.objects.filter(
            produto_servico="Trat. Superficial"
        ).order_by("nome")
        self.fields["codigo_brasmol"].queryset = MateriaPrimaCatalogo.objects.filter(tipo="Tratamento").order_by("codigo")
        self.fields["setor"].queryset = Departamentos.objects.filter(ativo=True).order_by("nome")

        if not self.instance.pk:
            self.fields["data"].initial = now().date()



    def clean_observacoes(self):
        observacoes = self.cleaned_data.get("observacoes")
        if not observacoes:
            raise forms.ValidationError("O campo observações é obrigatório.")
        return observacoes
