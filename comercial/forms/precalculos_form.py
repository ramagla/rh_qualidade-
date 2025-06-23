# comercial/forms/precalculos.py
from django import forms
from comercial.models.precalculo import (
    PreCalculoMaterial, PreCalculoServicoExterno, RegrasCalculo,
    RoteiroCotacao, CotacaoFerramenta, AvaliacaoTecnica,
    AnaliseComercial, Desenvolvimento
)


from django import forms
from comercial.models.precalculo import PreCalculoMaterial
from tecnico.models.roteiro import RoteiroProducao
from django.forms import HiddenInput


class PreCalculoMaterialForm(forms.ModelForm):
    class Meta:
        model = PreCalculoMaterial
        exclude = ('cotacao', 'created_at', 'updated_at', 'created_by', 'updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        # Oculta o campo roteiro (preenchido automaticamente na view)
        if 'roteiro' in self.fields:
            self.fields['roteiro'].required = False  # ⚠️ ESSENCIAL para evitar erro!
            self.fields['roteiro'].widget = HiddenInput()

        # Campo código como somente leitura e usado no AJAX
        if 'codigo' in self.fields:
            self.fields['codigo'].required = False  # ⚠️ ESSENCIAL para evitar erro de validação
            self.fields['codigo'].widget.attrs.update({
                'class': 'form-control form-control-sm codigo-input',
                'readonly': 'readonly',
            })

        # Campo status, agora opcional para resolver erro de validação
        if 'status' in self.fields:
            self.fields['status'].required = False
            self.fields['status'].widget.attrs.update({
                'class': 'form-control form-control-sm'
            })

        # Campo ICMS (%)
        if 'icms' in self.fields:
            self.fields['icms'].widget.attrs.update({
                'class': 'form-control form-control-sm',
                'placeholder': '0.00'
            })
            self.fields['icms'].required = False

        # Campos opcionais com estilos consistentes
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


    


class PreCalculoServicoExternoForm(forms.ModelForm):
    class Meta:
        model = PreCalculoServicoExterno
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

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

class AvaliacaoTecnicaForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoTecnica
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Permite "Não aplicável" como escolha nula
        self.fields['seguranca'].required = False
        self.fields['requisito_especifico'].required = False

        # Garante que o valor "" seja convertido em None
        self.fields['seguranca'].empty_value = None
        self.fields['requisito_especifico'].empty_value = None

class AnaliseComercialForm(forms.ModelForm):
    class Meta:
        model = AnaliseComercial
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

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
        fields = ['observacoes_materiais']
        widgets = {
            'observacoes_materiais': CKEditor5Widget(config_name='default'),
        }

