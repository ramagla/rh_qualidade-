from django import forms
from django.core.exceptions import ValidationError
from tecnico.models.roteiro import RoteiroProducao
from django_ckeditor_5.widgets import CKEditor5Widget
from qualidade_fornecimento.models.fornecedor import FornecedorQualificado  # ✅ Correto
from comercial.models import Item  # ✅ Import direto

class RoteiroProducaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroProducao
        fields = [
            "item", "tipo_roteiro", "status", "peso_unitario_gramas",
            "revisao", "observacoes_gerais", "fontes_homologadas"
        ]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select select2"}),
            "tipo_roteiro": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "peso_unitario_gramas": forms.NumberInput(attrs={"class": "form-control", "step": "0.0000001"}),
            "observacoes_gerais": CKEditor5Widget(config_name="default"),
            "fontes_homologadas": forms.SelectMultiple(attrs={"class": "form-select select2", "multiple": "multiple"}),
        }
        labels = {
            "status": "Status",
            "observacoes_gerais": "Observações Gerais",
            "fontes_homologadas": "Fontes Homologadas",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["fontes_homologadas"].queryset = FornecedorQualificado.objects.all()
        self.fields["fontes_homologadas"].disabled = True  # ✅ Torna somente leitura

        item = self.initial.get("item") or self.data.get("item") or getattr(self.instance, "item", None)

        if item:
            try:
                item_obj = Item.objects.get(pk=item) if not isinstance(item, Item) else item
                if not self.instance.pk:
                    self.fields["fontes_homologadas"].initial = item_obj.fontes_homologadas.all()
            except Item.DoesNotExist:
                pass


    def clean(self):
        cleaned = super().clean()
        item = cleaned.get("item")
        tipo = cleaned.get("tipo_roteiro")
        if item and tipo:
            qs = RoteiroProducao.objects.filter(
                item=item,
                tipo_roteiro=tipo
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "Já existe um roteiro para este item e tipo de roteiro."
                )
        return cleaned
