from django import forms
from qualidade_fornecimento.models import FornecedorQualificado

class FornecedorQualificadoForm(forms.ModelForm):
    class Meta:
        model = FornecedorQualificado
        fields = [
            'nome',
            'produto_servico',
            'data_homologacao',
            'tipo_certificacao',
            'vencimento_certificacao',
            'risco',
            'data_avaliacao_risco',
            'proxima_avaliacao_risco',
            'tipo_formulario',
            'data_auditoria',
            'proxima_auditoria',
            'nota_auditoria',
            'especialista_nome',
            'especialista_contato',
            'certificado_anexo',
        ]
        widgets = {
            'produto_servico': forms.Select(attrs={'class': 'form-select'}),
            'tipo_certificacao': forms.Select(attrs={'class': 'form-select'}),
            'risco': forms.Select(attrs={'class': 'form-select'}),
            'tipo_formulario': forms.Select(attrs={'class': 'form-select'}),
            'data_homologacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'vencimento_certificacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_avaliacao_risco': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'proxima_avaliacao_risco': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_auditoria': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'proxima_auditoria': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nota_auditoria': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',   # permite decimais
                'min': '0',
                'max': '100'
            }),
            'especialista_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'especialista_contato': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formata os campos de data para o formato ISO (YYYY-MM-DD) para os inputs type="date"
        if self.instance:
            if self.instance.data_homologacao:
                self.initial['data_homologacao'] = self.instance.data_homologacao.strftime('%Y-%m-%d')
            if self.instance.vencimento_certificacao:
                self.initial['vencimento_certificacao'] = self.instance.vencimento_certificacao.strftime('%Y-%m-%d')
            if self.instance.data_avaliacao_risco:
                self.initial['data_avaliacao_risco'] = self.instance.data_avaliacao_risco.strftime('%Y-%m-%d')
            if self.instance.data_auditoria:
                self.initial['data_auditoria'] = self.instance.data_auditoria.strftime('%Y-%m-%d')
        
        # Remover obrigatoriedade dos campos quando:
        # Produto for "Calibração" e Tipo de Certificação for "NBR-ISO 17025 RBC"
        data = self.data or self.initial
        produto = data.get('produto_servico') or (self.instance.produto_servico if self.instance else None)
        certificacao = data.get('tipo_certificacao') or (self.instance.tipo_certificacao if self.instance else None)
        if produto == "Calibração" and certificacao == "NBR-ISO 17025 RBC":
            for field in [
                'vencimento_certificacao', 'risco', 'data_avaliacao_risco',
                'proxima_avaliacao_risco', 'tipo_formulario', 'data_auditoria',
                'proxima_auditoria', 'nota_auditoria', 'especialista_nome', 'especialista_contato'
            ]:
                if field in self.fields:
                    self.fields[field].required = False

    def clean_nota_auditoria(self):
        raw_nota = self.data.get('nota_auditoria')
        if raw_nota:
            # Substitui vírgula por ponto, caso seja usado como separador decimal
            raw_nota = raw_nota.replace(',', '.')
            try:
                nota = float(raw_nota)
            except ValueError:
                raise forms.ValidationError("Valor inválido para a nota da auditoria. Use um número decimal (ex: 85.3).")
            if nota < 0 or nota > 100:
                raise forms.ValidationError("A nota da auditoria deve estar entre 0 e 100 (ex: 85 para 85%).")
            self.cleaned_data['nota_auditoria'] = nota
            return nota
        return None
