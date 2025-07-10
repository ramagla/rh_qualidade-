# comercial/forms/precalculos.py
from django import forms
from comercial.models.precalculo import (
    PreCalculoMaterial, PreCalculoServicoExterno, RegrasCalculo,
    RoteiroCotacao, CotacaoFerramenta, AvaliacaoTecnica,
    AnaliseComercial, Desenvolvimento
)
from decimal import Decimal
from django.db.models import Q


from django import forms
from comercial.models.precalculo import PreCalculoMaterial
from tecnico.models.roteiro import InsumoEtapa, RoteiroProducao
from django.forms import HiddenInput


class PreCalculoMaterialForm(forms.ModelForm):
    class Meta:
        model = PreCalculoMaterial
        exclude = (
            'cotacao', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            'descricao', 'unidade', 'nome_materia_prima'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Oculta o campo roteiro
        self.fields['roteiro'].required = False
        self.fields['roteiro'].widget = forms.HiddenInput()

        # Campo código (readonly, preenchido via JS)
        self.fields['codigo'].required = False
        self.fields['codigo'].widget.attrs.update({
            'class': 'form-control form-control-sm codigo-input',
            'readonly': 'readonly',
        })

        # Campo status
        self.fields['status'].required = False
        self.fields['status'].widget.attrs.update({
            'class': 'form-control form-control-sm'
        })

        # Campo ICMS
        self.fields['icms'].required = False
        self.fields['icms'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'placeholder': '0.00'
        })

        # Campos com estilos
        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'icms', 'preco_kg',
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto'
        ]
        for campo in campos:
            if campo in self.fields:
                widget = self.fields[campo].widget
                css = (
                    'form-select form-select-sm'
                    if isinstance(widget, forms.Select)
                    else 'form-control form-control-sm'
                )
                self.fields[campo].required = False
                self.fields[campo].widget.attrs.update({'class': css})

        # Corrige exibição como 0E-7 → 0.000
        if self.instance and self.instance.pk:
            for campo in ['peso_liquido', 'peso_bruto', 'desenvolvido_mm']:
                valor = getattr(self.instance, campo, None)
                if isinstance(valor, Decimal):
                    self.initial[campo] = f"{valor:.3f}"

    def clean(self):
        cleaned_data = super().clean()
        campos_decimal = [
            'lote_minimo', 'entrega_dias', 'icms', 'preco_kg',
            'peso_liquido', 'peso_bruto', 'desenvolvido_mm'
        ]
        for campo in campos_decimal:
            valor = cleaned_data.get(campo)
            if valor in ["", None]:
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
        exclude = (
            'cotacao', 'created_at', 'updated_at',
            'created_by', 'updated_by',
            'nome_insumo', 'codigo_materia_prima',
            'descricao_materia_prima', 'unidade',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtra insumos de Tratamento Externo ou Oleamento
        self.fields['insumo'].queryset = InsumoEtapa.objects.filter(
            Q(etapa__setor__nome__icontains="Tratamento Externo") |
            Q(etapa__setor__nome__icontains="Oleamento")
        )
        self.fields['insumo'].required = True
        self.fields['insumo'].widget = forms.HiddenInput()
        self.fields['insumo'].label = "Insumo"

        # Campo STATUS: torna opcional e estiliza
        if 'status' in self.fields:
            self.fields['status'].required = False
            self.fields['status'].widget.attrs.update({
                'class': 'form-control form-control-sm'
            })

        # Campo ICMS
        if 'icms' in self.fields:
            self.fields['icms'].widget.attrs.update({
                'class': 'form-control form-control-sm',
                'placeholder': '0.00'
            })
            self.fields['icms'].required = False

        # Campos de compra: optional e estilizados
        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'icms', 'preco_kg',
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto'
        ]
        for campo in campos:
            if campo in self.fields:
                widget = self.fields[campo].widget
                css_class = (
                    'form-select form-select-sm'
                    if widget.__class__.__name__ == 'Select'
                    else 'form-control form-control-sm'
                )
                self.fields[campo].widget.attrs.update({'class': css_class})
                self.fields[campo].required = False

        # Corrige exibição de decimais
        if self.instance and self.instance.pk:
            for campo in ['peso_liquido', 'peso_bruto', 'desenvolvido_mm']:
                valor = getattr(self.instance, campo, None)
                if isinstance(valor, Decimal):
                    self.initial[campo] = f"{valor:.3f}"




class RegrasCalculoForm(forms.ModelForm):
    class Meta:
        model = RegrasCalculo
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

class RoteiroCotacaoForm(forms.ModelForm):
    class Meta:
        model = RoteiroCotacao
        exclude = ('precalculo', 'cotacao', 'created_at', 'updated_at', 'created_by', 'updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos visuais e ocultos
        campos_visuais = ['pph', 'setup_minutos', 'custo_hora', 'custo_total']
        for campo in campos_visuais:
            if campo in self.fields:
                self.fields[campo].required = False
                self.fields[campo].widget.attrs.update({
                    'class': 'form-control form-control-sm text-center'
                })

        # Oculta o campo etapa, mas mantém no POST
        if 'etapa' in self.fields:
            self.fields['etapa'].required = False
            self.fields['etapa'].widget = forms.HiddenInput()


from django_ckeditor_5.widgets import CKEditor5Widget

# comercial/forms/precalculos_form.py

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from comercial.models.precalculo import CotacaoFerramenta

class CotacaoFerramentaForm(forms.ModelForm):
    class Meta:
        model = CotacaoFerramenta
        fields = "__all__"
        widgets = {
            "observacoes": CKEditor5Widget(config_name="default", attrs={"class": "ckeditor"}),
        }

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

        self.fields['seguranca'].required = False
        self.fields['requisito_especifico'].required = False

        # Isso ajuda a evitar erro de conversão direta
        self.fields['seguranca'].empty_value = None
        self.fields['requisito_especifico'].empty_value = None

    def clean(self):
        cleaned_data = super().clean()

        for campo in ['seguranca', 'requisito_especifico']:
            valor = cleaned_data.get(campo)

            if valor in [None, '', 'None']:
                cleaned_data[campo] = None
            elif valor in ['True', True, '1', 1]:
                cleaned_data[campo] = True
            elif valor in ['False', False, '0', 0]:
                cleaned_data[campo] = False

        return cleaned_data


class AnaliseComercialForm(forms.ModelForm):
    class Meta:
        model = AnaliseComercial
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'motivo_reprovacao': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = 'andamento'


class DesenvolvimentoForm(forms.ModelForm):
    class Meta:
        model = Desenvolvimento
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')


from django import forms
from comercial.models.precalculo import PreCalculo
from django_ckeditor_5.widgets import CKEditor5Widget

from django_ckeditor_5.widgets import CKEditor5Widget

class PreCalculoForm(forms.ModelForm):
    class Meta:
        model = PreCalculo
        fields = ['observacoes_materiais',"observacoes_servicos",]
        widgets = {
            'observacoes_materiais': CKEditor5Widget(config_name='default'),
            'observacoes_servicoes': CKEditor5Widget(config_name='default'),

        }

from django import forms
from decimal import Decimal, InvalidOperation
from comercial.models.precalculo import PreCalculo

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



