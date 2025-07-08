# comercial/forms/precalculos.py
from django import forms
from comercial.models.precalculo import (
    PreCalculoMaterial, PreCalculoServicoExterno, RegrasCalculo,
    RoteiroCotacao, CotacaoFerramenta, AvaliacaoTecnica,
    AnaliseComercial, Desenvolvimento
)
from decimal import Decimal


from django import forms
from comercial.models.precalculo import PreCalculoMaterial
from tecnico.models.roteiro import InsumoEtapa, RoteiroProducao
from django.forms import HiddenInput


class PreCalculoMaterialForm(forms.ModelForm):
    class Meta:
        model = PreCalculoMaterial
        exclude = ('cotacao', 'created_at', 'updated_at', 'created_by', 'updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Oculta o campo roteiro
        if 'roteiro' in self.fields:
            self.fields['roteiro'].required = False
            self.fields['roteiro'].widget = HiddenInput()

        # Campo código como somente leitura
        if 'codigo' in self.fields:
            self.fields['codigo'].required = False
            self.fields['codigo'].widget.attrs.update({
                'class': 'form-control form-control-sm codigo-input',
                'readonly': 'readonly',
            })

        # Campo status
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

        # Campos com estilos
        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'preco_kg',
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto'
        ]
        for campo in campos:
            if campo in self.fields:
                self.fields[campo].required = False
                self.fields[campo].widget.attrs.update({
                    'class': 'form-control form-control-sm'
                })

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


    


class PreCalculoServicoExternoForm(forms.ModelForm):
    class Meta:
        model = PreCalculoServicoExterno
        exclude = ('cotacao', 'created_at', 'updated_at', 'created_by', 'updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['insumo'].queryset = InsumoEtapa.objects.filter(
            etapa__setor__nome__icontains="Tratamento Externo"
        )
        self.fields['insumo'].required = True
        self.fields['insumo'].widget = forms.HiddenInput()
        self.fields['insumo'].label = "Insumo"

        campos = [
            'lote_minimo', 'entrega_dias', 'fornecedor', 'preco_kg',
            'desenvolvido_mm', 'peso_liquido', 'peso_bruto'
        ]
        for campo in campos:
            if campo in self.fields:
                widget = self.fields[campo].widget
                css_class = "form-select form-select-sm" if widget.__class__.__name__ == "Select" else "form-control form-control-sm"
                self.fields[campo].widget.attrs.update({"class": css_class})
                self.fields[campo].required = False

        # ✅ Corrige exibição como 0E-7 → 0.000
        if self.instance and self.instance.pk:
            from decimal import Decimal
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
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

class CotacaoFerramentaForm(forms.ModelForm):
    class Meta:
        model = CotacaoFerramenta
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

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

class PrecoFinalForm(forms.ModelForm):
    class Meta:
        model = PreCalculo
        fields = ['preco_selecionado', 'preco_manual']
        widgets = {
            'preco_manual': forms.NumberInput(attrs={
                'class': 'form-control text-end',
                'placeholder': 'Digite o preço manual'
            }),
        }


