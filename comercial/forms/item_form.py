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
        fields = '__all__'


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
            "data_revisao": DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),
            "codigo_desenho": TextInput(attrs={"class": "form-control", "placeholder": "Código do desenho"}),
            "status": Select(attrs={"class": "form-select"}),
            "seguranca_mp": CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_ts": CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_m1": CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_l1": CheckboxInput(attrs={"class": "form-check-input"}),
            "seguranca_l2": CheckboxInput(attrs={"class": "form-check-input"}),

            "simbolo_mp": FileInput(attrs={"class": "form-control"}),
            "simbolo_ts": FileInput(attrs={"class": "form-control"}),
            "simbolo_m1": FileInput(attrs={"class": "form-control"}),
            "simbolo_l1": FileInput(attrs={"class": "form-control"}),
            "simbolo_l2": FileInput(attrs={"class": "form-control"}),
            "codigo_amostra": TextInput(attrs={"class": "form-control", "placeholder": "Código de amostra"}),
            "tipo_item": Select(attrs={"class": "form-select"}),
            "fontes_homologadas": forms.SelectMultiple(attrs={"class": "form-select select2", "data-placeholder": "Selecione as fontes homologadas"}),

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
           "seguranca_mp": "Possui MP",
            "seguranca_ts": "Possui TS",
            "seguranca_m1": "Possui M1",
            "seguranca_l1": "Possui L1",
            "seguranca_l2": "Possui L2",

            "simbolo_mp": "Imagem MP",
            "simbolo_ts": "Imagem TS",
            "simbolo_m1": "Imagem M1",
            "simbolo_l1": "Imagem L1",
            "simbolo_l2": "Imagem L2",
            "codigo_amostra": "Código de Amostra",

                "tipo_item": "Tipo de Item",
"fontes_homologadas": "Fontes Homologadas",

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
            if not codigo_desenho:
                self.add_error("codigo_desenho", "Obrigatório para itens de cotação.")
            else:
                cleaned_data["codigo"] = codigo_desenho
                self.data = self.data.copy()
                self.data["codigo"] = codigo_desenho

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
