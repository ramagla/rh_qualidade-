# comercial/views/handlers/analise_handler.py

from django.utils import timezone
from comercial.forms.precalculos_form import AnaliseComercialForm

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
            obj.precalculo      = precalc
            obj.usuario         = request.user
            obj.assinatura_nome = request.user.get_full_name() or request.user.username
            obj.assinatura_cn   = request.user.email
            obj.data_assinatura = timezone.now()
            obj.save()
            return True, form

    # 3) em todos os outros casos, retorna False + form populado
    return False, form
