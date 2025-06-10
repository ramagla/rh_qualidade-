from django.forms import inlineformset_factory

from qualidade_fornecimento.forms.rolo_forms import RoloMateriaPrimaForm
from qualidade_fornecimento.models.materiaPrima import RelacaoMateriaPrima
from qualidade_fornecimento.models.rolo import RoloMateriaPrima

RoloFormSet = inlineformset_factory(
    parent_model=RelacaoMateriaPrima,
    model=RoloMateriaPrima,
    form=RoloMateriaPrimaForm,
    fk_name="tb050",  # ✅ ESSA LINHA É FUNDAMENTAL NO SEU CASO
    extra=0,
    can_delete=True,
)