# comercial/forms/precalculos.py
from django import forms
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
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto', 'peso_bruto_total'
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

        if 'peso_bruto_total' in self.fields:
            self.fields['peso_bruto_total'].widget = TextInput(
                attrs={
                    'class': 'form-control form-control-sm text-end peso-bruto-total',
                    'readonly': 'readonly',
                }
            )

        if 'desenvolvido_mm' in self.fields:
            self.fields['desenvolvido_mm'].widget = TextInput(
                attrs={
                    'class': 'form-control form-control-sm',
                }
            )

        if self.instance and self.instance.pk:
            for campo in ['peso_liquido', 'peso_bruto', 'peso_bruto_total', 'desenvolvido_mm']:
                valor = getattr(self.instance, campo, None)
                if isinstance(valor, Decimal):
                    self.initial[campo] = f"{valor:.3f}"

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




class RegrasCalculoForm(forms.ModelForm):
    class Meta:
        model = RegrasCalculo
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

from comercial.models.centro_custo import CentroDeCusto

class RoteiroCotacaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroCotacao
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define NumberInput com attrs diretamente (mais seguro que .update)
        campos_numericos = ['pph', 'setup_minutos', 'custo_hora', 'custo_total']
        for campo in campos_numericos:
            self.fields[campo].required = False
            self.fields[campo].widget = forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-center',
                'autocomplete': 'off'
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



class AnaliseComercialForm(forms.ModelForm):
    class Meta:
        model = AnaliseComercial
        exclude = ('cotacao', 'created_at', 'updated_at', 'created_by', 'updated_by')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'motivo_reprovacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['status'].initial = 'andamento'

        # ⚙️ Campo booleano novo - capacidade produtiva
        self.fields['capacidade_produtiva'].required = False
        self.fields['capacidade_produtiva'].widget = forms.Select(
            choices=[
                ('', '---------'),  # opção em branco
                ('True', 'Sim'),
                ('False', 'Não'),
            ],
            attrs={'class': 'form-select form-select-sm'}
        )




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
        fields = ['preco_selecionado', 'preco_manual']
        widgets = {
            'preco_manual': forms.TextInput(attrs={
                'class': 'form-control text-end',
                'placeholder': 'Ex: 32.000,00'
            }),
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



