from decimal import Decimal
from django.forms import inlineformset_factory
from django.utils import timezone

from comercial.forms.precalculos_form import RoteiroCotacaoForm
from comercial.models.precalculo import PreCalculo, RoteiroCotacao


def processar_aba_roteiro(request, precalc):
    # ———————————————— 1) Cria linhas iniciais ————————————————
    if not precalc.roteiro_item.exists() and hasattr(precalc, "analise_comercial_item"):
        item = precalc.analise_comercial_item.item
        if hasattr(item, "roteiro"):
            roteiro = item.roteiro
            qtde = precalc.analise_comercial_item.qtde_estimada or 1

            for etapa in roteiro.etapas.select_related("setor"):
                pph         = etapa.pph or 1
                setup       = etapa.setup_minutos or 0
                custo_hora  = etapa.setor.custo_atual or 0

                try:
                    tempo_pecas = Decimal(qtde) / Decimal(pph)
                except ZeroDivisionError:
                    tempo_pecas = Decimal(0)
                tempo_setup = Decimal(setup) / Decimal(60)
                total       = (tempo_pecas + tempo_setup) * Decimal(custo_hora)

                RoteiroCotacao.objects.create(
                    precalculo      = precalc,
                    etapa           = etapa.etapa,
                    setor           = etapa.setor,
                    pph             = pph,
                    setup_minutos   = setup,
                    custo_hora      = custo_hora,
                    custo_total     = round(total, 2),
                    usuario         = request.user,
                    assinatura_nome = request.user.get_full_name() or request.user.username,
                    assinatura_cn   = request.user.email,
                    data_assinatura = timezone.now(),
                )

    # ———————————————— 2) Monta o formset ————————————————
    RotSet = inlineformset_factory(
        PreCalculo,
        RoteiroCotacao,
        form=RoteiroCotacaoForm,
        extra=0,
        can_delete=False,
    )

    fs_rot = RotSet(
        request.POST if request.method == "POST" and "form_roteiro_submitted" in request.POST else None,
        instance=precalc,
        prefix="rot"
    )

    # ———————————————— 3) Injeta custo_hora para exibição ————————————————
    print("ERROS DO FORMSET:")
    for form in fs_rot.forms:
        print(form.errors)
        if hasattr(form.instance, 'setor') and form.instance.setor_id and not hasattr(form.instance, 'custo_hora'):
            form.instance.custo_hora = getattr(form.instance.setor, "custo_atual", 0)

    # ———————————————— 4) Salva se foi submetido ————————————————
    if request.method == "POST" and "form_roteiro_submitted" in request.POST:
                if fs_rot.is_valid():
                    instancias = fs_rot.save(commit=False)
                    alguma_alteracao = False

                    for i, obj in enumerate(instancias):
                        form = fs_rot.forms[i]

                        if form.has_changed():
                            obj.precalculo = precalc
                            obj.usuario = request.user
                            obj.assinatura_nome = request.user.get_full_name() or request.user.username
                            obj.assinatura_cn = request.user.email
                            obj.data_assinatura = timezone.now()
                            obj.save()
                            alguma_alteracao = True

                    if alguma_alteracao:
                        fs_rot.save_m2m()
                        return True, fs_rot
                    else:
                        from django.contrib import messages
                        messages.error(request, "Nenhuma alteração válida foi identificada para salvar.")
                        return False, fs_rot
                else:
                    from django.contrib import messages
                    messages.error(request, "Corrija os erros no formulário de Roteiro.")
                    return False, fs_rot
        
    return False, fs_rot
