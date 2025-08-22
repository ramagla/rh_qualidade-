from django import forms

from qualidade_fornecimento.models import FornecedorQualificado

from django.core.files.uploadedfile import UploadedFile
from django.forms import FileInput

class FornecedorQualificadoForm(forms.ModelForm):
    class Meta:
        model = FornecedorQualificado
        fields = [
            "nome",
            "produto_servico",
            "data_homologacao",
            "tipo_certificacao",
            "vencimento_certificacao",
            "risco",
            "data_avaliacao_risco",
            "proxima_avaliacao_risco",
            "tipo_formulario",
            "data_auditoria",
            "proxima_auditoria",
            "nota_auditoria",
            "especialista_nome",
            "especialista_contato",
            "especialista_cargo",
            "certificado_anexo",
            "lead_time",
            "ativo",
        ]
        widgets = {
            "certificado_anexo": FileInput(
                attrs={
                    "id": "id_certificado_anexo",
                    "class": "d-none",              # input real escondido
                    "accept": ".pdf,.png,.jpg,.jpeg"  # opcional
                }
            ),
        
            "produto_servico": forms.Select(attrs={"class": "form-select"}),
            "tipo_certificacao": forms.Select(attrs={"class": "form-select"}),
            "risco": forms.Select(attrs={"class": "form-select"}),
            "tipo_formulario": forms.Select(attrs={"class": "form-select"}),
            "data_homologacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "vencimento_certificacao": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_avaliacao_risco": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "proxima_avaliacao_risco": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_auditoria": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "proxima_auditoria": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nota_auditoria": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",  # permite decimais
                    "min": "0",
                    "max": "100",
                }
            ),
            "especialista_nome": forms.TextInput(attrs={"class": "form-control"}),
            "especialista_cargo": forms.TextInput(attrs={"class": "form-control"}),
            "especialista_contato": forms.TextInput(attrs={"class": "form-control"}),
            "lead_time": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "ativo": forms.Select(attrs={"class": "form-select select2"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formata os campos de data para o formato ISO (YYYY-MM-DD) para os inputs type="date"
        if self.instance:
            if self.instance.data_homologacao:
                self.initial["data_homologacao"] = (
                    self.instance.data_homologacao.strftime("%Y-%m-%d")
                )
            if self.instance.vencimento_certificacao:
                self.initial["vencimento_certificacao"] = (
                    self.instance.vencimento_certificacao.strftime("%Y-%m-%d")
                )
                # 🔹 Garante que avaliação de risco = vencimento
                self.initial["data_avaliacao_risco"] = (
                    self.instance.vencimento_certificacao.strftime("%Y-%m-%d")
                )
            if self.instance.data_auditoria:
                self.initial["data_auditoria"] = self.instance.data_auditoria.strftime(
                    "%Y-%m-%d"
                )

        # Remover obrigatoriedade dos campos quando:
        # Produto for "Calibração" e Tipo de Certificação for "NBR-ISO 17025 RBC"
        data = self.data or self.initial
        produto = data.get("produto_servico") or (
            self.instance.produto_servico if self.instance else None
        )
        certificacao = data.get("tipo_certificacao") or (
            self.instance.tipo_certificacao if self.instance else None
        )
        if (produto == "Calibração" and certificacao == "NBR-ISO 17025 RBC") or produto == "Material do Cliente":
            for field in [
                "data_homologacao", 
                "vencimento_certificacao",
                "risco",
                "data_avaliacao_risco",
                "proxima_avaliacao_risco",
                "tipo_formulario",
                "data_auditoria",
                "proxima_auditoria",
                "nota_auditoria",
                "especialista_nome",
                "especialista_contato",
            ]:
                if field in self.fields:
                    self.fields[field].required = False

    def clean_nota_auditoria(self):
        raw_nota = self.data.get("nota_auditoria")
        if raw_nota:
            # Substitui vírgula por ponto, caso seja usado como separador decimal
            raw_nota = raw_nota.replace(",", ".")
            try:
                nota = float(raw_nota)
            except ValueError:
                raise forms.ValidationError(
                    "Valor inválido para a nota da auditoria. Use um número decimal (ex: 85.3)."
                )
            if nota < 0 or nota > 100:
                raise forms.ValidationError(
                    "A nota da auditoria deve estar entre 0 e 100 (ex: 85 para 85%)."
                )
            self.cleaned_data["nota_auditoria"] = nota
            return nota
        return None
    
    def clean_certificado_anexo(self):
        f = self.cleaned_data.get("certificado_anexo")
        if isinstance(f, UploadedFile) and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("O arquivo excede 5 MB.")
        return f
    
    def clean(self):
        cleaned_data = super().clean()
        vencimento = cleaned_data.get("vencimento_certificacao")
        if vencimento:
            cleaned_data["data_avaliacao_risco"] = vencimento
        return cleaned_data

