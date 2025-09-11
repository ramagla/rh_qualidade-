# qualidade_fornecimento/forms/estoque_intermediario_forms.py — PARA (ajuste do queryset de LOTE + filtro MP)
from decimal import Decimal
from django import forms

from qualidade_fornecimento.models import (
    EstoqueIntermediario,
    MateriaPrimaCatalogo,
    RoloMateriaPrima,  # ✅ necessário para filtrar o queryset do lote
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
            "op", "materia_prima", "lote", "tb050",
            "qtde_op_prevista", "pecas_planejadas_op",
            "enviado", "maquina",
            "data_envio",         

            "observacoes", "anexo",
            "tolerancia_sucata_percentual", "custo_kg",
        ]
        widgets = {
            "op": forms.TextInput(attrs={"class": "form-control"}),
            "materia_prima": forms.Select(attrs={"class": "form-select select2"}),
            "lote": forms.Select(attrs={"class": "form-select select2"}),
            "tb050": forms.Select(attrs={"class": "form-select select2"}),
            "qtde_op_prevista": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "pecas_planejadas_op": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "enviado": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "maquina": forms.Select(attrs={"class": "form-select select2"}),
            "observacoes": OBS_WIDGET,
            "tolerancia_sucata_percentual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "custo_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "data_envio": forms.DateTimeInput(attrs={"type":"datetime-local","class":"form-control"}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🔎 Filtra apenas MPs do tipo "Materia-Prima"
        self.fields["materia_prima"].queryset = MateriaPrimaCatalogo.objects.filter(tipo="Materia-Prima")

        # ✅ MUITO IMPORTANTE: o queryset do LOTE precisa bater com a MP informada
        mp_id = None
        if self.data.get("materia_prima"):
            mp_id = self.data.get("materia_prima")
        elif getattr(self.instance, "materia_prima_id", None):
            mp_id = self.instance.materia_prima_id

        if mp_id:
            self.fields["lote"].queryset = (
                RoloMateriaPrima.objects.filter(tb050__materia_prima_id=mp_id).order_by("-nro_rolo")
            )
        else:
            self.fields["lote"].queryset = RoloMateriaPrima.objects.none()

    def clean_pecas_planejadas_op(self):
        v = self.cleaned_data["pecas_planejadas_op"]
        if v <= 0:
            raise forms.ValidationError("Peças planejadas deve ser > 0.")
        return v


class ApontarRetornoForm(forms.ModelForm):
    class Meta:
        model = EstoqueIntermediario
        fields = ["pecas_apontadas", "sucata", "refugo", "retorno", "observacoes", "anexo", "justificativa_excesso", "data_retorno", ]
        widgets = {
            "pecas_apontadas": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "sucata": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "refugo": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "retorno": forms.NumberInput(attrs={"class": "form-control", "step": "0.001", "min": "0"}),
            "observacoes": OBS_WIDGET,
            "justificativa_excesso": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Obrigatória se % sucata > tolerância."}),
            "data_retorno": forms.DateTimeInput(attrs={"type":"datetime-local","class":"form-control"}),

        }