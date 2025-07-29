from comercial.forms.precalculos_form import AvaliacaoTecnicaForm
from comercial.utils.assinatura_utils import criar_assinatura_eletronica
from django.utils import timezone

def processar_aba_avaliacao(request, precalc):
    instance = getattr(precalc, 'avaliacao_tecnica_item', None)
    form = AvaliacaoTecnicaForm(
        request.POST if request.method == "POST" else None,
        instance=instance
    )

    if request.method == "POST" and 'form_avaliacao_submitted' in request.POST:
        if form.is_valid():
            obj = form.save(commit=False)
            obj.precalculo = precalc
            obj.usuario = request.user  # ✅ define quem assinou
            obj.assinatura_nome = request.user.get_full_name()
            obj.assinado_em = timezone.now()
            obj.save()

            criar_assinatura_eletronica(obj)  # 🔐 gera hash e salva no modelo AssinaturaEletronica

            return True, form

        else:
            print("❌ ERROS NO FORMULARIO DE AVALIAÇÃO:")
            print(form.errors)  # <== Adicione isso para ver os erros do form
            return False, form

    return False, form

