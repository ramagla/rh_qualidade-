from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory

from qualidade_fornecimento.models.estoque_intermediario import (
    EstoqueIntermediario,
    EstoqueIntermediarioItem,
)
from qualidade_fornecimento.models import (
    MateriaPrimaCatalogo,
    RoloMateriaPrima,
    RelacaoMateriaPrima,
)

# ✅ Tenta usar CKEditor5; se não houver, usa Textarea com classe ckeditor5
try:
    from django_ckeditor_5.widgets import CKEditor5Widget
    OBS_WIDGET = CKEditor5Widget(config_name="default")
except Exception:
    OBS_WIDGET = forms.Textarea(attrs={"class": "form-control ckeditor5", "rows": 4})


class EstoqueIntermediarioForm(forms.ModelForm):
    class Meta:
        model = EstoqueIntermediario
        fields = [
            "op", "materia_prima",
            "qtde_op_prevista", "pecas_planejadas_op",
            "maquina", "data_envio",
            "observacoes", "anexo",
            "tolerancia_sucata_percentual", "custo_kg",
        ]
        widgets = {
            "op": forms.TextInput(attrs={"class": "form-control"}),
            "materia_prima": forms.Select(attrs={"class": "form-select select2"}),
            "qtde_op_prevista": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "pecas_planejadas_op": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "maquina": forms.Select(attrs={"class": "form-select select2"}),
            "observacoes": OBS_WIDGET,
            "tolerancia_sucata_percentual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "custo_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "data_envio": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local", "class": "form-control"},
            ),        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["materia_prima"].queryset = MateriaPrimaCatalogo.objects.filter(tipo="Materia-Prima")
        # garante parse e render no datetime-local
        self.fields["data_envio"].input_formats = [
            "%Y-%m-%dT%H:%M",       # HTML5 datetime-local
            "%Y-%m-%d %H:%M:%S",    # fallback
            "%d/%m/%Y %H:%M",       # se alguém digitar manualmente pt-BR
        ]
    def clean_pecas_planejadas_op(self):
        v = self.cleaned_data["pecas_planejadas_op"]
        if v <= 0:
            raise forms.ValidationError("Peças planejadas deve ser > 0.")
        return v
    
    def clean_op(self):
        op = (self.cleaned_data.get("op") or "").strip()
        if not op:
            return op
        qs = EstoqueIntermediario.objects.filter(
            op__iexact=op, status__in=("EM_FABRICA", "RETORNADO")
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "Já existe um envio para esta OP (em fábrica ou no histórico)."
            )
        return op


class EIItemForm(forms.ModelForm):
    """
    Item (lote/rolo) do envio.
    • Usa Select2+AJAX no LOTE: queryset vazio no GET.
    • No POST, limita a queryset ao valor selecionado para validar.
    • Labels “limpos”: lote = nro_rolo; tb050 = nro_relatorio.
    """
    class Meta:
        model = EstoqueIntermediarioItem
        fields = ["lote", "tb050", "enviado"]
        widgets = {
            "lote": forms.Select(attrs={"class": "form-select select2 eiitem-lote"}),
            "tb050": forms.Select(attrs={"class": "form-select select2 eiitem-tb50"}),
            "enviado": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔹 Label só com o número do rolo
        self.fields["lote"].label_from_instance = lambda obj: str(getattr(obj, "nro_rolo", obj.pk))
        # 🔹 Label só com o número do relatório TB050
        self.fields["tb50"] = self.fields.get("tb050")  # alias local
        if self.fields["tb50"]:
            self.fields["tb50"].label_from_instance = lambda obj: str(getattr(obj, "nro_relatorio", obj.pk))

        # 🔹 GET -> queryset vazia (carrega via AJAX); POST -> apenas o escolhido (para validar)
        selected = None
        if self.is_bound:
            selected = self.data.get(self.add_prefix("lote")) or None
        elif self.instance and self.instance.lote_id:
            selected = self.instance.lote_id

        if selected:
            self.fields["lote"].queryset = RoloMateriaPrima.objects.filter(pk=selected)
        else:
            self.fields["lote"].queryset = RoloMateriaPrima.objects.none()

    def clean(self):
        cleaned = super().clean()
        lote = cleaned.get("lote")
        if lote and not cleaned.get("tb050"):
            # autopreenche TB050 a partir do lote
            self.instance.tb050_id = getattr(lote, "tb050_id", None)
        return cleaned


class EIItemRetornoForm(forms.ModelForm):
    class Meta:
        model = EstoqueIntermediarioItem
        fields = ["retorno", "sucata", "refugo"]
        widgets = {
            "retorno": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "sucata":  forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "refugo":  forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
        }



# ==== Formsets ====
EIItemFormSet = inlineformset_factory(
    EstoqueIntermediario,
    EstoqueIntermediarioItem,
    form=EIItemForm,
    extra=2,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

EIItemRetornoFormSet = inlineformset_factory(
    EstoqueIntermediario,
    EstoqueIntermediarioItem,
    form=EIItemRetornoForm,
    extra=0,
    can_delete=False,
)


class ApontarRetornoForm(forms.ModelForm):
    class Meta:
        model = EstoqueIntermediario
        fields = [
            "pecas_apontadas",
            "observacoes", "anexo",
            "justificativa_excesso", "data_retorno",
        ]
        widgets = {
            "pecas_apontadas": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "observacoes": OBS_WIDGET,
            "justificativa_excesso": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Obrigatória se % sucata > tolerância."}
            ),
        "data_retorno": forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local", "class": "form-control"},
        )
        }

