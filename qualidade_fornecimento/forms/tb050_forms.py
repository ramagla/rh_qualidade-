from django import forms
from django.forms import DateInput

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo


class RelacaoMateriaPrimaForm(forms.ModelForm):
    nro_relatorio = forms.IntegerField(
        required=False,
        label="N° do Relatório",
        widget=forms.NumberInput(
            attrs={"readonly": "readonly", "class": "form-control"}
        ),
    )
    atraso_em_dias = forms.IntegerField(
        required=False,
        label="Atraso em Dias",
        widget=forms.NumberInput(
            attrs={"readonly": "readonly", "class": "form-control"}
        ),
    )
    demerito_ip = forms.IntegerField(
        required=False,
        label="Demérito (IP)",
        widget=forms.NumberInput(
            attrs={"readonly": "readonly", "class": "form-control"}
        ),
    )

    class Meta:
        model = RelacaoMateriaPrima
        fields = [
            "nro_relatorio",
            "materia_prima",
            "data_entrada",
            "fornecedor",
            "nota_fiscal",
            "numero_certificado",
            "item_seguranca",
            "material_cliente",
            "status",
            "data_prevista_entrega",
            "data_renegociada_entrega",
            "atraso_em_dias",
            "demerito_ip",
            "anexo_certificado",
        ]
        widgets = {
            "data_entrada": DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_prevista_entrega": DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_renegociada_entrega": DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nota_fiscal": forms.TextInput(attrs={"class": "form-control"}),
            "numero_certificado": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "item_seguranca": forms.Select(attrs={"class": "form-select"}),
            "material_cliente": forms.Select(attrs={"class": "form-select"}),
            "anexo_certificado": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance

        self.fields["status"].widget.attrs["readonly"] = True
        self.fields["status"].widget.attrs["disabled"] = True

        # Relacionamentos com labels customizadas
        self.fields["materia_prima"].queryset = (
            MateriaPrimaCatalogo.objects.all().order_by("codigo")
        )
        self.fields["materia_prima"].label_from_instance = (
            lambda obj: f"{obj.codigo} - {obj.descricao}"
        )

        self.fields["fornecedor"].queryset = (
            FornecedorQualificado.objects.all().order_by("nome")
        )
        self.fields["fornecedor"].label_from_instance = (
            lambda obj: f"{obj.nome}"
        )

        # Inicialização de campos readonly
        if instance.pk:
            self.fields["nro_relatorio"].initial = instance.nro_relatorio
            self.fields["atraso_em_dias"].initial = max(instance.atraso_em_dias or 0, 0)
            self.fields["demerito_ip"].initial = instance.demerito_ip or 0

            if instance.data_entrada:
                self.initial["data_entrada"] = instance.data_entrada.strftime("%Y-%m-%d")
            if instance.data_prevista_entrega:
                self.initial["data_prevista_entrega"] = instance.data_prevista_entrega.strftime("%Y-%m-%d")
            if instance.data_renegociada_entrega:
                self.initial["data_renegociada_entrega"] = instance.data_renegociada_entrega.strftime("%Y-%m-%d")

                
