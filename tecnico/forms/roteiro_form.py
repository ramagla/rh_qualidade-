from django import forms
from django.core.exceptions import ValidationError
from tecnico.models.roteiro import RoteiroProducao
from django_ckeditor_5.widgets import CKEditor5Widget

class RoteiroProducaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroProducao
        fields = ["item", "tipo_roteiro", "peso_unitario_gramas", "revisao", "observacoes_gerais"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select select2"}),
            "massa_mil_pecas": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "observacoes_gerais": CKEditor5Widget(config_name="default"),
        }
        labels = {
            "massa_mil_pecas": "Massa por 1.000 peças (kg)",
            "observacoes_gerais": "Observações Gerais",
        }

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
