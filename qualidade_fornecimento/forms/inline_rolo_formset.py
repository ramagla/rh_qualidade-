from django.forms import inlineformset_factory
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.rolo import RoloMateriaPrima
from qualidade_fornecimento.forms.rolo_forms import RoloMateriaPrimaForm

RoloFormSet = inlineformset_factory(
    parent_model=RelacaoMateriaPrima,  # ✅ Correto agora
    model=RoloMateriaPrima,
    form=RoloMateriaPrimaForm,
    extra=0,
    can_delete=True,
)
