from comercial.forms.precalculos_form import DesenvolvimentoForm
from comercial.utils.assinatura_utils import preencher_assinatura


def processar_aba_desenvolvimento(request, precalc):
    form = DesenvolvimentoForm(
        request.POST if request.method == "POST" else None,
        instance=getattr(precalc, 'desenvolvimento_item', None)
    )

    if request.method == "POST" and "form_desenvolvimento_submitted" in request.POST:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.precalculo = precalc
            preencher_assinatura(request, obj)
            obj.save()
            return True, form

    return False, form
