from decimal import Decimal
from django.utils import timezone

from comercial.forms.precalculos_form import RegrasCalculoForm
from comercial.models.precalculo import RegrasCalculo
from comercial.utils.assinatura_utils import criar_assinatura_eletronica


def processar_aba_regras(request, precalc):
    """
    Processa o formulário da aba Regras de Cálculo.
    Cria uma instância padrão se não existir.
    """

    # Cria regras de cálculo padrão se ainda não existir
    if not hasattr(precalc, "regras_calculo_item"):
        cot = precalc.cotacao
        RegrasCalculo.objects.create(
            precalculo=precalc,
            icms=cot.icms,
            pis=Decimal("0.65"),
            confins=Decimal("3.00"),
            ir=Decimal("1.20"),
            csll=Decimal("1.08"),
            df=Decimal("2.50"),
            dv=Decimal("5.00"),
            usuario=request.user,
            assinatura_nome=request.user.get_full_name() or request.user.username,
            assinatura_cn=request.user.email,
            data_assinatura=timezone.now(),
        )

    # Instancia o formulário com a instância agora garantida
    form = RegrasCalculoForm(
        request.POST if request.method == "POST" else None,
        instance=precalc.regras_calculo_item
    )

    if request.method == "POST" and "form_regras_submitted" in request.POST:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.precalculo = precalc
            criar_assinatura_eletronica(obj)
            obj.save()
            return True, form

    return False, form
