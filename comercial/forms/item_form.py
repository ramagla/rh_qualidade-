from django import forms
from comercial.models import Item
from django.forms.widgets import CheckboxInput, Select, TextInput, FileInput, DateInput


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
                "cliente", "codigo", "descricao", "ncm", "ipi",
                "ferramenta", "lote_minimo",
                "codigo_cliente", "descricao_cliente",
                "codigo_desenho",  # ⬅️ adicionado aqui
                "automotivo_oem", "requisito_especifico", "item_seguranca",
                "desenho", "revisao", "data_revisao",
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
            "ipi": TextInput(attrs={"class": "form-control", "placeholder": "Ex: 5.00"}),
            "codigo_desenho": TextInput(attrs={"class": "form-control", "placeholder": "Código do desenho"}),


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

        }
