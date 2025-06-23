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

class PreCalculoMaterialForm(forms.ModelForm):
    class Meta:
        model = PreCalculoMaterial
        exclude = ('cotacao','created_at','updated_at','created_by','updated_by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'roteiro' in self.fields:
            self.fields['roteiro'].queryset = self.fields['roteiro'].queryset.select_related('item')
            self.fields['roteiro'].widget.attrs.update({'class': 'form-select form-select-sm'})

        # Tornar campos opcionais
        self.fields['lote_minimo'].required = False
        self.fields['entrega_dias'].required = False
        self.fields['fornecedor'].required = False
        self.fields['preco_kg'].required = False



    


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
