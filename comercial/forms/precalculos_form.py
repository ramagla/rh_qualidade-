# comercial/forms/precalculos.py
from django import forms
from comercial.models.item import Item
from comercial.models.precalculo import (
    PreCalculoMaterial, PreCalculoServicoExterno, RegrasCalculo,
    RoteiroCotacao, CotacaoFerramenta, AvaliacaoTecnica,
    AnaliseComercial, Desenvolvimento
)
from decimal import Decimal
from django.db.models import Q

from django.forms import TextInput

from django import forms
from comercial.models.precalculo import PreCalculoMaterial
from tecnico.models.roteiro import InsumoEtapa, RoteiroProducao
from django.forms import HiddenInput
from django_ckeditor_5.widgets import CKEditor5Widget
from comercial.models.precalculo import PreCalculo


class PreCalculoMaterialForm(forms.ModelForm):
    class Meta:
        model = PreCalculoMaterial
        fields = '__all__'
        exclude = (
            'cotacao', 'created_at', 'updated_at',
            'created_by', 'updated_by',
        )       

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['roteiro'].required = False
        self.fields['roteiro'].widget = HiddenInput()

        self.fields['codigo'].required = False
        self.fields['codigo'].widget.attrs.update({
            'class': 'form-control form-control-sm codigo-input',
            'readonly': 'readonly',
        })

        self.fields['status'].required = False
        self.fields['status'].widget.attrs.update({
            'class': 'form-control form-control-sm'
        })

        self.fields['icms'].required = False
        self.fields['icms'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'placeholder': '0.00'
        })        

        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'icms',
            'preco_kg', 'desenvolvido_mm', 'peso_liquido', 'peso_bruto', 'peso_bruto_total'
        ]
        for campo in campos:
            if campo in self.fields:
                widget = self.fields[campo].widget
                css_class = (
                    'form-select form-select-sm'
                    if isinstance(widget, forms.Select)
                    else 'form-control form-control-sm'
                )
                self.fields[campo].required = False
                self.fields[campo].widget.attrs.update({'class': css_class})

        if 'peso_bruto_total' in self.fields:
            self.fields['peso_bruto_total'].widget = TextInput(
                attrs={
                    'class': 'form-control form-control-sm text-end peso-bruto-total',
                }
            )

        if not self.is_bound and self.instance and self.instance.pk:
            for campo in ['peso_liquido', 'peso_bruto', 'peso_bruto_total', 'desenvolvido_mm']:
                valor = getattr(self.instance, campo, None)
                if isinstance(valor, Decimal):
                    self.initial[campo] = str(valor)

    def has_changed(self):
        changed = super().has_changed()
        peso_bruto_total_str = self.data.get(self.add_prefix("peso_bruto_total"), "").strip()
        if not changed and peso_bruto_total_str and peso_bruto_total_str != "0,000":
            return True
        return changed

    def clean(self):
        cleaned_data = super().clean()

        campos_decimal = [
            'lote_minimo', 'entrega_dias', 'icms', 'preco_kg',
            'peso_liquido', 'peso_bruto', 'peso_bruto_total', 'desenvolvido_mm'
        ]

        for campo in campos_decimal:
            valor = cleaned_data.get(campo)
            if isinstance(valor, str):
                valor = valor.replace(".", "").replace(",", ".")
            try:
                cleaned_data[campo] = Decimal(valor) if valor not in [None, ''] else None
            except (ValueError, InvalidOperation):
                self.add_error(campo, f"Valor inválido em {campo}: {valor}")
                cleaned_data[campo] = None

        return cleaned_data







from django import forms
from decimal import Decimal
from django.db.models import Q
from comercial.models.precalculo import PreCalculoServicoExterno
from tecnico.models.roteiro import InsumoEtapa


class PreCalculoServicoExternoForm(forms.ModelForm):
    class Meta:
        model = PreCalculoServicoExterno
        fields = "__all__"
        exclude = (
            'cotacao', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            'nome_insumo', 'descricao_materia_prima', 'unidade',
        )
       

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['insumo'].queryset = InsumoEtapa.objects.filter(
            Q(etapa__setor__nome__icontains="Tratamento Externo") |
            Q(etapa__setor__nome__icontains="Oleamento")
        )
        self.fields['insumo'].required = True
        self.fields['insumo'].widget = forms.HiddenInput()
        self.fields['insumo'].label = "Insumo"

        self.fields['codigo_materia_prima'].required = False
        self.fields['codigo_materia_prima'].widget.attrs.update({
            'class': 'form-control form-control-sm codigo-input',
            'readonly': 'readonly',
        })

        if 'status' in self.fields:
            self.fields['status'].required = False
            self.fields['status'].widget.attrs.update({
                'class': 'form-control form-control-sm'
            })

        if 'icms' in self.fields:
            self.fields['icms'].required = False
            self.fields['icms'].widget.attrs.update({
                'class': 'form-control form-control-sm',
                'placeholder': '0.00'
            })

        
        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'icms', 'preco_kg',
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto', 'peso_liquido_total'

        ]
        for campo in campos:
            if campo in self.fields:
                widget = self.fields[campo].widget
                css_class = (
                    'form-select form-select-sm'
                    if isinstance(widget, forms.Select)
                    else 'form-control form-control-sm'
                )
                self.fields[campo].widget.attrs.update({'class': css_class})
                self.fields[campo].required = False

        if 'peso_liquido_total' in self.fields:
            self.fields['peso_liquido_total'].widget = TextInput(
                attrs={
                    'class': 'form-control form-control-sm text-end peso-liquido-total',
                    'readonly': 'readonly',
                }
            )

        if 'desenvolvido_mm' in self.fields:
            self.fields['desenvolvido_mm'].widget = TextInput(
                attrs={
                    'class': 'form-control form-control-sm',
                }
            )

        print(f"[DEBUG] Form init - PK: {self.instance.pk}, Bound: {self.is_bound}")
        for campo in ['peso_liquido', 'peso_bruto', 'desenvolvido_mm', 'peso_liquido_total']:
            if campo in self.fields:
                self.fields[campo].widget = TextInput(attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': '0,0000000'
                })




    def has_changed(self):
        changed = super().has_changed()
        peso_liquido_total_str = self.data.get(self.add_prefix("peso_liquido_total"), "").strip()
        if not changed and peso_liquido_total_str and peso_liquido_total_str != "0,00000":
            return True
        return changed

    def clean(self):
        cleaned_data = super().clean()

        campos_decimal = [
            'lote_minimo', 'entrega_dias', 'icms', 'preco_kg',
            'peso_liquido', 'peso_bruto', 'peso_liquido_total', 'desenvolvido_mm'
        ]


        for campo in campos_decimal:
            valor = cleaned_data.get(campo)
            if isinstance(valor, str):
                valor = valor.replace(".", "").replace(",", ".")
            try:
                cleaned_data[campo] = Decimal(valor) if valor not in [None, ''] else None
            except (ValueError, InvalidOperation):
                self.add_error(campo, f"Valor inválido em {campo}: {valor}")
                cleaned_data[campo] = None

        return cleaned_data




class RegrasCalculoForm(forms.ModelForm):
    class Meta:
        model = RegrasCalculo
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

from comercial.models.centro_custo import CentroDeCusto

class RoteiroCotacaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroCotacao
        exclude = ('maquinas_roteiro', 'nome_acao', 'precalculo', 'usuario', 'assinatura_nome', 'assinatura_cn', 'data_assinatura')

        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define NumberInput com attrs diretamente (mais seguro que .update)
        campos_numericos = ['pph', 'setup_minutos', 'custo_hora', 'custo_total']
        for campo in campos_numericos:
            self.fields[campo].required = False
            self.fields[campo].widget = forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-center',
                'autocomplete': 'off',
                'step': '1' if campo == 'pph' else '0.0001',  # ⬅️ Aqui está o controle das casas decimais
                'min': '0'
            })

        # Etapa como campo oculto
        if 'etapa' in self.fields:
            self.fields['etapa'].required = False
            self.fields['etapa'].widget = forms.HiddenInput()

        # Garante que setor está visível com queryset válido
        if 'setor' in self.fields:
            self.fields['setor'].queryset = CentroDeCusto.objects.all()
            self.fields['setor'].required = False
            self.fields['setor'].widget.attrs.update({
                'class': 'form-control form-control-sm text-center',
                'autocomplete': 'off'
            })

       





from django_ckeditor_5.widgets import CKEditor5Widget

# comercial/forms/precalculos_form.py

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from comercial.models.precalculo import CotacaoFerramenta

class CotacaoFerramentaForm(forms.ModelForm):
    class Meta:
        model = CotacaoFerramenta
        fields = "__all__"
       

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ferramenta'].widget.attrs.update({
            "class": "form-select select2"
        })
        self.fields['ferramenta'].label = "Ferramenta"



class AvaliacaoTecnicaForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoTecnica
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        placeholders = {
            "possui_projeto_obs": "Descreva se há projeto...",
            "precisa_dispositivo_obs": "Dispositivo necessário? Qual?",
            "caracteristicas_criticas_obs": "Detalhe as características críticas...",
            "precisa_amostras_obs": "Quantas amostras? Para quê?",
            "restricao_dimensional_obs": "Há restrições dimensionais?",
            "acabamento_superficial_obs": "Especificar acabamento desejado...",
            "validacao_metrologica_obs": "Como será feita a validação?",
            "rastreabilidade_obs": "Descreva a rastreabilidade exigida...",
            "item_aparencia_obs": "Quais requisitos de aparência?",
            "fmea_obs": "Existe análise FMEA?",
            "teste_solicitado_obs": "Detalhe os testes solicitados...",
            "lista_fornecedores_obs": "Indique fornecedores aprovados...",
            "normas_disponiveis_obs": "Liste normas aplicáveis...",
            "requisitos_regulamentares_obs": "Detalhe os requisitos legais...",
            "requisitos_adicionais_obs": "Há exigências extras?",
            "metas_a_obs": "Meta de tipo A (se aplicável)...",
            "metas_b_obs": "Meta de tipo B...",
            "metas_c_obs": "Meta de tipo C...",
            "metas_d_obs": "Meta de tipo D...",
            "metas_confiabilidade_obs": "Detalhe a meta de confiabilidade...",
            "seguranca_obs": "Quais aspectos de segurança são exigidos?",
            "requisito_especifico_obs": "Existe algum requisito específico?",
        }


        campos_bool = [
            'possui_projeto', 'precisa_dispositivo', 'caracteristicas_criticas',
            'precisa_amostras', 'restricao_dimensional', 'acabamento_superficial',
            'validacao_metrologica', 'rastreabilidade', 'item_aparencia', 'fmea',
            'teste_solicitado', 'lista_fornecedores', 'normas_disponiveis',
            'requisitos_regulamentares', 'requisitos_adicionais', 'metas_a',
            'metas_b', 'metas_c', 'metas_confiabilidade', 'metas_d',
            'seguranca', 'requisito_especifico'
        ]

        opcoes = [
            (None, "Não aplicável"),
            (True, "Sim"),
            (False, "Não"),
        ]

        for campo in campos_bool:
            if campo in self.fields:
                self.fields[campo].required = False
                self.fields[campo].widget = forms.Select(
                    choices=opcoes,
                    attrs={'class': 'form-select form-select-sm'}
                )

        for campo, texto in placeholders.items():
            if campo in self.fields:
                self.fields[campo].widget.attrs['placeholder'] = texto



from comercial.models.item import Item  # garantir o import correto


from comercial.models import Item
from django import forms

class ItemInlineForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "codigo", "descricao", "ncm", "lote_minimo", "revisao", "data_revisao", "ipi",
            "automotivo_oem", "requisito_especifico", "item_seguranca"
        ]

    def clean_codigo(self):
        codigo = self.cleaned_data.get("codigo")
        if not codigo:
            raise forms.ValidationError("O campo 'Código do Desenho' é obrigatório.")
        return codigo



from django import forms
from comercial.models.precalculo import AnaliseComercial
from comercial.models import Item
from tecnico.models.roteiro import RoteiroProducao


class AnaliseComercialForm(forms.ModelForm):
    class Meta:
        model = AnaliseComercial
        exclude = ('precalculo', 'created_at', 'updated_at', 'created_by', 'updated_by')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }

    def __init__(self, *args, **kwargs):
        cotacao = kwargs.pop("cotacao", None)
        edicao = kwargs.pop("edicao", False)
        super().__init__(*args, **kwargs)

        # Valor inicial para status
        self.fields['status'].initial = 'andamento'

        # Capacidade produtiva com select customizado
        self.fields['capacidade_produtiva'].required = False
        self.fields['capacidade_produtiva'].widget = forms.Select(
            choices=[
                ('', '---------'),
                ('True', 'Sim'),
                ('False', 'Não'),
            ],
            attrs={'class': 'form-select form-select-sm'}
        )

        # Se não for edição, remove obrigatoriedade dos campos ocultos no cadastro
        if not edicao:
            campos_opcionais = [
                'conclusao', 'consideracoes', 'motivo_reprovacao',
                'material_fornecido', 'material_fornecido_obs',
                'requisitos_entrega', 'requisitos_entrega_obs',
                'requisitos_pos_entrega', 'requisitos_pos_entrega_obs',
                'requisitos_comunicacao', 'requisitos_comunicacao_obs',
                'requisitos_notificacao', 'requisitos_notificacao_obs',
                'especificacao_embalagem', 'especificacao_embalagem_obs',
                'especificacao_identificacao', 'especificacao_identificacao_obs',
                'tipo_embalagem', 'tipo_embalagem_obs',
            ]
            for campo in campos_opcionais:
                if campo in self.fields:
                    self.fields[campo].required = False

        # Aplica o filtro de itens por cliente, se houver cotação
        if cotacao:
            cliente = cotacao.cliente
            queryset_filtrado = Item.objects.filter(cliente=cliente, status="Ativo").order_by("codigo")

            self.fields['item'] = forms.ModelChoiceField(
                queryset=queryset_filtrado,
                widget=forms.Select(attrs={
'class': 'form-select form-select-sm campo-analise'
                }),
                required=True,
                empty_label="---------"
            )

            # Corrige item inválido se estiver relacionado a outro cliente
            if (
                self.instance and self.instance.pk and
                self.instance.item and self.instance.item.cliente != cliente
            ):
                print("⚠️ Resetando item não relacionado ao cliente da cotação.")
                self.initial['item'] = None
                self.fields["item"].required = False  # Evita erro se item vier vazio

            # Campo ROTEIRO vinculado ao item (via AJAX ou instância)
            self.fields["roteiro_selecionado"] = forms.ModelChoiceField(
                queryset=RoteiroProducao.objects.none(),
                required=False,
                label="Roteiro Selecionado",
                widget=forms.Select(attrs={
                    "class": "form-select form-select-sm select2 campo-analise"
                })
            )

            # Se item já preenchido, mostra roteiros disponíveis
            item_id = self.data.get("item") or getattr(self.instance, "item_id", None)
            if item_id:
                try:
                    roteiros = RoteiroProducao.objects.filter(item_id=item_id)
                    self.fields["roteiro_selecionado"].queryset = roteiros
                except Exception:
                    pass

        # Placeholders para campos *_obs
        placeholders = {
            "material_fornecido_obs": "Descreva o material fornecido...",
            "requisitos_entrega_obs": "Qual a frequência de entrega?",
            "requisitos_pos_entrega_obs": "Há alguma exigência adicional?",
            "requisitos_comunicacao_obs": "Qual o meio de comunicação? Ex: e-mail",
            "requisitos_notificacao_obs": "Como será feita a notificação?",
            "especificacao_embalagem_obs": "Ex: caixa padrão, plástico bolha...",
            "especificacao_identificacao_obs": "Ex: etiqueta, impressão direta...",
            "tipo_embalagem_obs": "Tipo de embalagem recomendada",
        }
        for nome_campo, texto in placeholders.items():
            if nome_campo in self.fields:
                self.fields[nome_campo].widget.attrs['placeholder'] = texto

        print("🧪 Itens disponíveis no select:", list(self.fields['item'].queryset))

    def clean_item(self):
        item_pk = self.cleaned_data.get('item')

        if item_pk == "__novo__":
            raise forms.ValidationError("Salve o novo item antes de prosseguir.")

        if isinstance(item_pk, Item):
            return item_pk

        try:
            return Item.objects.get(pk=item_pk)
        except (TypeError, ValueError, Item.DoesNotExist):
            raise forms.ValidationError("Selecione um item válido.")








class DesenvolvimentoForm(forms.ModelForm):
    class Meta:
        model = Desenvolvimento
        fields = ["completo", "consideracoes"]

        widgets = {
            "completo": forms.RadioSelect(choices=[(True, "Sim"), (False, "Não")]),
            "consideracoes": CKEditor5Widget(config_name="default"),
        }

class PreCalculoForm(forms.ModelForm):
    class Meta:
        model = PreCalculo
        fields = [
            'observacoes_materiais',
            'observacoes_servicos',
            'observacoes_roteiro',
        ]
        widgets = {            
            'observacoes_materiais': CKEditor5Widget(config_name='default'),
            'observacoes_servicos': CKEditor5Widget(config_name='default'),
            'observacoes_roteiro': CKEditor5Widget(config_name='default'),
        }

from django import forms
from decimal import Decimal, InvalidOperation

class PrecoFinalForm(forms.ModelForm):
    class Meta:
        model = PreCalculo
        fields = ['preco_selecionado', 'preco_manual', 'observacoes_precofinal']
        widgets = {
            'preco_manual': forms.TextInput(attrs={
                'class': 'form-control text-end',
                'placeholder': 'Ex: 0,0049'
            }),     
            'observacoes_precofinal': CKEditor5Widget(config_name='default'),      
        }

    def clean_preco_manual(self):
        data = self.cleaned_data.get('preco_manual')
        if data:
            try:
                return Decimal(str(data).replace(".", "").replace(",", "."))
            except (InvalidOperation, ValueError):
                raise forms.ValidationError("Preço manual inválido.")
        return Decimal("0.00")

    def clean_preco_selecionado(self):
        data = self.cleaned_data.get("preco_selecionado")
        if not data:
            return Decimal("0.00")
        try:
            # Substitui vírgula por ponto se ainda vier assim
            valor = Decimal(str(data).replace(",", ".")).quantize(Decimal("0.01"))
            return valor
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Preço selecionado inválido.")



