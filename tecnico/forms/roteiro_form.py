from django import forms
from django.core.exceptions import ValidationError
from tecnico.models.roteiro import RoteiroProducao

class RoteiroProducaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroProducao
        fields = ["item"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select select2"}),
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
