from django import forms
from comercial.models.ordem_desenvolvimento import OrdemDesenvolvimento
from tecnico.models.maquina import Maquina
from tecnico.models.roteiro import RoteiroProducao


class OrdemDesenvolvimentoForm(forms.ModelForm):
    DOCUMENTOS_CHOICES = OrdemDesenvolvimento.DOCUMENTOS
    familia_produto = forms.ChoiceField(
            choices=[(k, v) for k, v in Maquina.FAMILIA_PRODUTO_LABELS.items()],
            widget=forms.Select(attrs={"class": "form-select select2"}),
            required=False,
            label="Família de Produto"
        )
    documentos_producao = forms.MultipleChoiceField(
        choices=DOCUMENTOS_CHOICES,
        widget=forms.SelectMultiple(attrs={"class": "form-select select2"}),
        required=False,
        label="Documentos de produção"
    )

    class Meta:
        model = OrdemDesenvolvimento
        exclude = [
                "numero", "created_at", "created_by", "updated_at", "updated_by",
                "assinatura_comercial_nome", "assinatura_comercial_email", "assinatura_comercial_data",
                "assinatura_tecnica_nome", "assinatura_tecnica_email", "assinatura_tecnica_data",
            ]
        widgets = {
            "precalculo": forms.Select(attrs={"class": "form-select"}),
            "item": forms.Select(attrs={"class": "form-select"}),
            "email_ppap": forms.EmailInput(attrs={"class": "form-control"}),
            "codigo_brasmol": forms.TextInput(attrs={"class": "form-control"}),
            "prazo_solicitado": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),
            "qtde_amostra": forms.NumberInput(attrs={"class": "form-control"}),
            "razao": forms.Select(attrs={"class": "form-select"}),

            # Técnicos
            "familia_produto": forms.Select(attrs={"class": "form-select"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "revisar_pir": forms.Select(attrs={"class": "form-select"}),
            "aprovado": forms.Select(attrs={"class": "form-select"}),
            "prazo_material": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "rotinas_sistema": forms.Select(attrs={"class": "form-select"}),
            "prazo_rotinas": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),
            "prazo_docs": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "ferramenta": forms.Select(attrs={"class": "form-select"}),
            "tipo_ferramenta": forms.Select(attrs={"class": "form-select"}),
            "os_ferramenta": forms.NumberInput(attrs={"class": "form-control"}),
            "prazo_ferramental": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "dispositivo": forms.Select(attrs={"class": "form-select"}),
            "tipo_dispositivo": forms.Select(attrs={"class": "form-select"}),
            "os_dispositivo": forms.NumberInput(attrs={"class": "form-control"}),
            "prazo_dispositivo": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "amostra": forms.Select(attrs={"class": "form-select"}),
            "numero_op": forms.NumberInput(attrs={"class": "form-control"}),
            "prazo_amostra": forms.DateInput(format="%Y-%m-%d", attrs={"class": "form-control", "type": "date"}),

            "tratamento_termico": forms.Select(attrs={"class": "form-select"}),
            "tipo_tte": forms.Select(attrs={"class": "form-select"}),
            "status_tte": forms.Select(attrs={"class": "form-select"}),
            "prazo_tte": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "tratamento_superficial": forms.Select(attrs={"class": "form-select"}),
            "tipo_tse": forms.Select(attrs={"class": "form-select"}),
            "status_tse": forms.Select(attrs={"class": "form-select"}),
            "prazo_tse": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),
            "codigo_amostra": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: AM-2025-001"}),

            "resistencia_corrosao": forms.Select(attrs={"class": "form-select"}),
            "prazo_resistencia": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

            "durabilidade": forms.Select(attrs={"class": "form-select"}),
            "prazo_durabilidade": forms.DateInput(format="%Y-%m-%d",attrs={"class": "form-control", "type": "date"}),

        }

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # ⚙️ Preenche os valores como lista (para edição)
            if self.instance and self.instance.documentos_producao:
                self.initial["documentos_producao"] = self.instance.documentos_producao.split(",")

            # ⛔ Campos somente leitura
            for field in [
                "cliente", "automotivo_oem", "comprador", "requisito_especifico",
                "item_seguranca", "codigo_desenho", "revisao", "data_revisao",
                "metodologia_aprovacao"
            ]:
                if field in self.fields:
                    self.fields[field].widget.attrs["readonly"] = True
                    self.fields[field].widget.attrs["class"] = "form-control-plaintext"

            # 🆕 Preencher Família de Produto automaticamente (só em novo)
            if not self.instance.pk:
                # obtém o pré-cálculo vinculado
                precalc = self.initial.get("precalculo") or getattr(self.instance, "precalculo", None)
                if precalc:
                    # busca o roteiro aprovado para o item
                    roteiro = RoteiroProducao.objects.filter(
                        item=precalc.item,
                        aprovado=True
                    ).prefetch_related("etapas__propriedades__maquinas").first()

                    if roteiro:
                        # pega apenas a PRIMEIRA etapa
                        primeira_etapa = roteiro.etapas.order_by("id").first()
                        if primeira_etapa and hasattr(primeira_etapa, "propriedades"):
                            # máquinas vinculadas a essa etapa
                            maquinas = primeira_etapa.propriedades.maquinas.all()
                            if maquinas.exists():
                                # pega a primeira máquina e define seu grupo
                                self.initial["familia_produto"] = maquinas.first().grupo_de_maquinas



    def clean_documentos_producao(self):
        # 🔄 Junta os múltiplos valores como string separada por vírgula
        return ",".join(self.cleaned_data.get("documentos_producao", []))
