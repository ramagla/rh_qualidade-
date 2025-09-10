from django import forms
from qualidade_fornecimento.models import Inventario, Contagem

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ["titulo", "descricao", "data_corte", "tipo"]  # 👈 inclui tipo
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "data_corte": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),  # 👈 select MP/PA
        }

class ContagemForm(forms.ModelForm):
    class Meta:
        model = Contagem
        fields = ["origem_qrcode", "quantidade"]  # ordem: QR primeiro
        widgets = {
            "origem_qrcode": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Leia/cole o QRCode aqui",
                "autofocus": "autofocus",
            }),
            "quantidade": forms.NumberInput(attrs={
                "class": "form-control form-control-lg",
                "step": "0.0001",
                "inputmode": "decimal",
            }),
        }
