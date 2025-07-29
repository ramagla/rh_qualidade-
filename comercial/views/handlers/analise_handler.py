# comercial/views/handlers/analise_handler.py

from django.utils import timezone
from comercial.forms.precalculos_form import AnaliseComercialForm
from comercial.utils.assinatura_utils import criar_assinatura_eletronica


def processar_aba_analise(request, precalc):
    """
    Exibe sempre o form com os dados já salvos em GET (ou em posts de outras abas),
    e só bind/valida em POST se for esse submit.
    """
    # detecta se veio deste tab
    submitted = "form_analise_submitted" in request.POST

    # 1) constrói SEM request.POST para GET e para POSTs de outros tabs
    instance = getattr(precalc, "analise_comercial_item", None)
    form = AnaliseComercialForm(None, instance=instance)

    # 2) se for ESTE submit, rebinda e salva
    if request.method == "POST" and submitted:
        form = AnaliseComercialForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.usuario = request.user
            obj.assinatura_nome = request.user.get_full_name()
            obj.assinado_em = timezone.now()
            obj.save()

            criar_assinatura_eletronica(obj)
            return True, form

    # 3) em todos os outros casos, retorna False + form populado
    return False, form
