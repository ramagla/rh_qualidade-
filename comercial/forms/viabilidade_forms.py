from django import forms
from comercial.models.viabilidade import ViabilidadeAnaliseRisco
from django_ckeditor_5.widgets import CKEditor5Widget
from django.forms.widgets import DateInput, TextInput, RadioSelect

# 🔁 Reutilizável: radios para booleanos
RADIO_SIM_NAO = [(True, "Sim"), (False, "Não")]

class ViabilidadeAnaliseRiscoForm(forms.ModelForm):
    class Meta:
        model = ViabilidadeAnaliseRisco
        fields = [
            "precalculo", "cliente", "requisito_especifico", "automotivo_oem", "item_seguranca",
            "codigo_desenho",

            "produto_definido", "risco_comercial",
            "conclusao_comercial", "consideracoes_comercial",
            "assinatura_comercial_nome", "assinatura_comercial_departamento", "assinatura_comercial_data",

            "capacidade_fabricacao", "custo_transformacao", "custo_ferramental", "metodo_alternativo",
            "risco_logistico", "conclusao_custos", "consideracoes_custos",
            "responsavel_custos", "departamento_custos", "data_custos",

            "recursos_suficientes", "atende_especificacoes", "atende_tolerancias",
            "capacidade_processo", "permite_manuseio", "precisa_cep", "cep_usado_similares",
            "processos_estaveis", "capabilidade_ok", "atende_requisito_cliente", "risco_tecnico",
            "conclusao_tecnica", "consideracoes_tecnicas",
            "responsavel_tecnica", "departamento_tecnica", "data_tecnica",
        ]
        widgets = {
            # Textos ricos
            "consideracoes_comercial": CKEditor5Widget(config_name="default"),
            "consideracoes_custos": CKEditor5Widget(config_name="default"),
            "consideracoes_tecnicas": CKEditor5Widget(config_name="default"),

            # Datas
            "data_custos": DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_tecnica": DateInput(attrs={"type": "date", "class": "form-control"}),
            "assinatura_comercial_data": DateInput(attrs={"type": "date", "class": "form-control"}),

            # Radios: Custos (imagem PDF)
            "capacidade_fabricacao": RadioSelect(choices=RADIO_SIM_NAO),
            "custo_transformacao": RadioSelect(choices=RADIO_SIM_NAO),
            "custo_ferramental": RadioSelect(choices=RADIO_SIM_NAO),
            "metodo_alternativo": RadioSelect(choices=RADIO_SIM_NAO),
            "risco_logistico": RadioSelect(choices=RADIO_SIM_NAO),

            # Switches padrão (restante)
           # Radios Sim/Não para todas as perguntas (inclusive técnica e comercial)
            **{
                field: RadioSelect(choices=RADIO_SIM_NAO)
                for field in [
                    "produto_definido", "risco_comercial",
                    "recursos_suficientes", "atende_especificacoes", "atende_tolerancias",
                    "capacidade_processo", "permite_manuseio", "precisa_cep", "cep_usado_similares",
                    "processos_estaveis", "capabilidade_ok", "atende_requisito_cliente", "risco_tecnico",
                ]
            },

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tentar obter o item vinculado via análise comercial
        item = None
        if self.instance and getattr(self.instance, "precalculo", None):
            ac = getattr(self.instance.precalculo, "analise_comercial_item", None)
            if ac and getattr(ac, "item", None):
                item = ac.item

        # Campo dinâmico: Número da Peça (só leitura)
        numero_peca = item.descricao if item else ""
        self.fields["numero_peca"] = forms.CharField(
            label="Número da Peça",
            required=False,
            disabled=True,
            initial=numero_peca,
            widget=TextInput(attrs={"class": "form-control", "readonly": True})
        )

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Popula os dados herdados do item do pré-cálculo
        ac = getattr(instance.precalculo, "analise_comercial_item", None)
        if ac and getattr(ac, "item", None):
            item = ac.item
            instance.cliente = item.cliente
            instance.requisito_especifico = item.requisito_especifico
            instance.automotivo_oem = item.automotivo_oem
            instance.item_seguranca = item.item_seguranca
            instance.codigo_desenho = item.codigo_desenho
            instance.revisao = item.revisao
            instance.data_desenho = item.data_revisao
            instance.codigo_brasmol = item.codigo

        if commit:
            instance.save()
        return instance
