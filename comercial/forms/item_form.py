from django import forms
from comercial.models import Item
from comercial.models.clientes import Cliente  # ⬅️ importa o modelo Cliente
from django.forms.widgets import CheckboxInput, Select, TextInput, FileInput, DateInput
from decimal import Decimal

class ItemForm(forms.ModelForm):
    ipi = forms.CharField(
        required=False,
        label="IPI (%)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: 9,75"})
    )
    class Meta:
        model = Item
        fields = [
            "cliente", "codigo", "descricao", "ncm", "ipi",
            "ferramenta", "lote_minimo",
            "codigo_cliente", "descricao_cliente",
            "codigo_desenho",
            "automotivo_oem", "requisito_especifico", "item_seguranca",
            "simbolo_seguranca",  # novo
            "status",             # novo
            "desenho", "revisao", "data_revisao",
            "tipo_item",

        ]

        widgets = {
            "cliente": Select(attrs={"class": "form-select select2"}),
            "ferramenta": Select(attrs={"class": "form-select select2"}),
            "codigo": TextInput(attrs={"class": "form-control", "placeholder": "Código interno"}),
            "descricao": TextInput(attrs={"class": "form-control", "placeholder": "Descrição do item"}),
            "ncm": TextInput(attrs={"class": "form-control", "placeholder": "NCM"}),
            "lote_minimo": TextInput(attrs={"class": "form-control", "type": "number", "min": "1"}),
            "codigo_cliente": TextInput(attrs={"class": "form-control", "placeholder": "Código no cliente"}),
            "descricao_cliente": TextInput(attrs={"class": "form-control", "placeholder": "Descrição no cliente"}),
            "automotivo_oem": CheckboxInput(attrs={"class": "form-check-input"}),
            "requisito_especifico": CheckboxInput(attrs={"class": "form-check-input"}),
            "item_seguranca": CheckboxInput(attrs={"class": "form-check-input"}),
            "desenho": FileInput(attrs={"class": "form-control"}),
            "revisao": TextInput(attrs={"class": "form-control", "placeholder": "Ex: A, B1"}),
            "data_revisao": DateInput(attrs={"class": "form-control", "type": "date"}),
            "codigo_desenho": TextInput(attrs={"class": "form-control", "placeholder": "Código do desenho"}),
            "status": Select(attrs={"class": "form-select"}),
            "simbolo_seguranca": FileInput(attrs={"class": "form-control"}),
            "tipo_item": Select(attrs={"class": "form-select"}),

        }

        labels = {
            "cliente": "Cliente",
            "codigo": "Código Interno",
            "descricao": "Descrição",
            "ncm": "NCM",
            "ferramenta": "Ferramenta Vinculada",
            "lote_minimo": "Lote Mínimo",
            "codigo_cliente": "Código no Cliente",
            "descricao_cliente": "Descrição no Cliente",
            "automotivo_oem": "Automotivo OEM",
            "requisito_especifico": "Requisito Específico Cliente?",
            "item_seguranca": "É Item de Segurança?",
            "desenho": "Arquivo de Desenho",
            "revisao": "Revisão",
            "data_revisao": "Data da Revisão",
            "codigo_desenho": "Código do Desenho",
                "status": "Status do Item",
    "simbolo_seguranca": "Imagem de Simbologia de Segurança",
    "tipo_item": "Tipo de Item",

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔍 Filtra apenas os clientes com tipo_cadastro = Cliente
        self.fields['cliente'].queryset = Cliente.objects.filter(tipo_cadastro='Cliente').order_by('razao_social')
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.razao_social} ({obj.cnpj})"

    def clean(self):
        cleaned_data = super().clean()
        tipo_item = cleaned_data.get("tipo_item")
        codigo_desenho = cleaned_data.get("codigo_desenho")

        if tipo_item == "cotacao":
            cleaned_data["codigo"] = codigo_desenho  # força a cópia
            self.data = self.data.copy()
            self.data["codigo"] = codigo_desenho  # atualiza o valor no POST para refletir no template

        return cleaned_data


    def clean_ipi(self):
            valor = self.cleaned_data.get("ipi")

            if valor in [None, ""]:
                return None  # campo vazio permitido

            if isinstance(valor, str):
                valor = valor.replace(",", ".")

            try:
                return Decimal(valor)
            except Exception:
                raise forms.ValidationError("Informe um número válido para o IPI (use ponto ou vírgula).")
