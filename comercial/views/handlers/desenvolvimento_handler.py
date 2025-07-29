from comercial.forms.precalculos_form import DesenvolvimentoForm
from comercial.utils.assinatura_utils import criar_assinatura_eletronica


def processar_aba_desenvolvimento(request, precalc):
    form = DesenvolvimentoForm(
        request.POST if request.method == "POST" else None,
        instance=getattr(precalc, 'desenvolvimento_item', None)
    )

    if request.method == "POST" and "form_desenvolvimento_submitted" in request.POST:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.precalculo = precalc
            obj.usuario = request.user
            obj.save()

            criar_assinatura_eletronica(obj)

            return True, form

    return False, form
