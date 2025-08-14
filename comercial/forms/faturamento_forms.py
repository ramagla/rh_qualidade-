from django import forms
from datetime import datetime
from decimal import Decimal, InvalidOperation

from comercial.models.faturamento import FaturamentoRegistro
from comercial.models.clientes import Cliente


class BRDecimalField(forms.DecimalField):
    """
    Aceita '1.234,56' e '1234,56' e converte para Decimal('1234.56').
    """
    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace('.', '').replace(',', '.')
        return super().to_python(value)


class FaturamentoRegistroForm(forms.ModelForm):
    # Campo de data armazenado como string no model, validado/mostrado em dd/mm/yyyy
    ocorrencia = forms.CharField(
        label="Ocorrência (dd/mm/yyyy)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "dd/mm/yyyy"})
    )

    # Código usado para vincular ao Cliente.cod_bm (sync/save fazem o match)
    cliente_codigo = forms.CharField(
        label="Código do Cliente",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: C35"})
    )

    # Nome livre do cliente (quando vier da fonte externa)
    cliente = forms.CharField(
        label="Cliente",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Cliente"})
    )

    # Select de clientes (FK)
    cliente_vinculado = forms.ModelChoiceField(
        label="Cliente Vinculado",
        queryset=Cliente.objects.all().order_by("cod_bm"),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select select2",
                "data-placeholder": "Selecione o cliente",
                "style": "width:100%"
            }
        ),
    )

    congelado = forms.BooleanField(
        label="Congelado (não atualizar via sync)",
        required=False,
        widget=forms.CheckboxInput()
    )

    item_quantidade = forms.IntegerField(
        label="Quantidade",
        required=False,
        min_value=0
    )
    item_valor_unitario = BRDecimalField(
        label="Valor Unitário (R$)",
        required=False,
        max_digits=14,
        decimal_places=4
    )
    item_ipi = BRDecimalField(
        label="IPI (%)",
        required=False,
        max_digits=6,
        decimal_places=2
    )
    perc_icms = BRDecimalField(
        label="ICMS (%) (NF)",
        required=False,
        max_digits=6,
        decimal_places=2
    )
    valor_frete = BRDecimalField(
        label="Valor Frete (R$)",
        required=False,
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        model = FaturamentoRegistro
        fields = [
            "nfe", "ocorrencia",
            "cliente_codigo", "cliente", "cliente_vinculado",
            "valor_frete",
            "item_codigo", "item_quantidade", "item_valor_unitario", "item_ipi", "perc_icms",
            "congelado",
            "tipo",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = kwargs.get("instance") or getattr(self, "instance", None)

        # Rótulo das opções do select: "CÓDIGO - Razão Social"
        self.fields["cliente_vinculado"].label_from_instance = (
            lambda obj: f"{(obj.cod_bm or '').upper()} - {obj.razao_social}"
        )

        # Quando NF-e estiver vazia, sugerir "Vale"
        if inst and (not inst.nfe or str(inst.nfe).strip() == ""):
            self.fields["nfe"].initial = "Vale"

        # Inicializar o select com o PK já vinculado (se houver)
        if inst and getattr(inst, "cliente_vinculado_id", None):
            self.fields["cliente_vinculado"].initial = inst.cliente_vinculado_id

        # Se a ocorrência vier ISO (YYYY-MM-DD) na instância, converter para dd/mm/yyyy
        try:
            oc = (getattr(inst, "ocorrencia", "") or "").strip()
            if "-" in oc and len(oc) >= 10:
                self.fields["ocorrencia"].initial = datetime.strptime(
                    oc[:10], "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
        except Exception:
            pass

    # Normaliza o código para facilitar o match (maiúsculas)
    def clean_cliente_codigo(self):
        v = (self.cleaned_data.get("cliente_codigo") or "").strip()
        return v.upper()

    # Validações numéricas
    def clean_ocorrencia(self):
        v = (self.cleaned_data.get("ocorrencia") or "").strip()
        if not v:
            return v
        try:
            dt = datetime.strptime(v, "%d/%m/%Y")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            raise forms.ValidationError("Use o formato dd/mm/yyyy.")

    def clean_item_valor_unitario(self):
        v = self.cleaned_data.get("item_valor_unitario")
        if v is None:
            return None
        try:
            return Decimal(v)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Valor unitário inválido.")

    def clean_item_ipi(self):
        v = self.cleaned_data.get("item_ipi")
        if v is None:
            return None
        if v < 0:
            raise forms.ValidationError("IPI não pode ser negativo.")
        return v

    def clean_perc_icms(self):
        v = self.cleaned_data.get("perc_icms")
        if v is None:
            return None
        if v < 0:
            raise forms.ValidationError("ICMS não pode ser negativo.")
        return v


    def clean(self):
        cleaned = super().clean()
        return cleaned
