from django.forms import inlineformset_factory
from tecnico.models.roteiro import RoteiroProducao, EtapaRoteiro, InsumoEtapa, PropriedadesEtapa
from tecnico.forms.etapa_form import EtapaRoteiroForm
from tecnico.forms.insumo_form import InsumoForm
from tecnico.forms.propriedades_form import PropriedadesEtapaForm

EtapaFormSet = inlineformset_factory(
    RoteiroProducao, EtapaRoteiro,
    form=EtapaRoteiroForm,
    extra=0, can_delete=True
)

InsumoFormSet = inlineformset_factory(
    EtapaRoteiro, InsumoEtapa,
    form=InsumoForm,
    extra=1, can_delete=True
)


PropriedadesFormSet = inlineformset_factory(
    EtapaRoteiro, PropriedadesEtapa,
    form=PropriedadesEtapaForm,
    extra=0, max_num=1, can_delete=False
)
