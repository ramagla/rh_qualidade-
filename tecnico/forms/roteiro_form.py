from django import forms
from django.core.exceptions import ValidationError
from tecnico.models.roteiro import RoteiroProducao
from django_ckeditor_5.widgets import CKEditor5Widget

class RoteiroProducaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroProducao
        fields = ["item", "massa_mil_pecas", "observacoes_gerais"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select select2"}),
            "massa_mil_pecas": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "observacoes_gerais": CKEditor5Widget(config_name="default"),
        }
        labels = {
            "massa_mil_pecas": "Massa por 1.000 peças (kg)",
            "observacoes_gerais": "Observações Gerais",
        }

    def clean_item(self):
        item = self.cleaned_data["item"]
        qs = RoteiroProducao.objects.filter(item=item)
        # se estivermos editando, exclui a instância atual
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Já existe um roteiro cadastrado para este item.")
        return item
