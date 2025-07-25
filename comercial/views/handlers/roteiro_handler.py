from decimal import Decimal
from django.forms import inlineformset_factory
from django.utils import timezone
from comercial.forms.precalculos_form import RoteiroCotacaoForm
from comercial.models.precalculo import PreCalculo, RoteiroCotacao
from tecnico.models.roteiro import EtapaRoteiro, PropriedadesEtapa
from django.contrib import messages


def processar_aba_roteiro(request, precalc, form_precalculo=None):
    if not precalc.roteiro_item.exists() and getattr(precalc, "analise_comercial_item", None):
        roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)


        if roteiro:
            qtde = precalc.analise_comercial_item.qtde_estimada or 1

            for etapa in roteiro.etapas.select_related("setor"):
                pph = etapa.pph or 1
                setup = etapa.setup_minutos or 0
                custo_hora = etapa.setor.custo_atual or 0

                try:
                    tempo_pecas = Decimal(qtde) / Decimal(pph)
                except ZeroDivisionError:
                    tempo_pecas = Decimal(0)

                tempo_setup = Decimal(setup) / Decimal(60)
                total = (tempo_pecas + tempo_setup) * Decimal(custo_hora)

                propriedades = PropriedadesEtapa.objects.filter(etapa=etapa).first()
                maquinas_roteiro = None
                nome_acao = None

                if propriedades:
                    maquinas = propriedades.maquinas.all()
                    maquinas_roteiro = ", ".join(m.codigo for m in maquinas)
                    nome_acao = propriedades.nome_acao

                RoteiroCotacao.objects.create(
                    precalculo=precalc,
                    etapa=etapa.etapa,
                    setor=etapa.setor,
                    pph=pph,
                    setup_minutos=setup,
                    custo_hora=custo_hora,
                    custo_total=round(total, 2),
                    usuario=request.user,
                    assinatura_nome=request.user.get_full_name() or request.user.username,
                    assinatura_cn=request.user.email,
                    data_assinatura=timezone.now(),
                    maquinas_roteiro=maquinas_roteiro,
                    nome_acao=nome_acao,
                )

    RotSet = inlineformset_factory(
        PreCalculo,
        RoteiroCotacao,
        form=RoteiroCotacaoForm,
        fields=(
            'setor',
            'etapa',
            'pph',
            'setup_minutos',
            'custo_hora',
            'custo_total',
            'maquinas_roteiro',       # ADICIONE
            'nome_acao',    
        ),
        extra=0,
        can_delete=False,
    )

    data = request.POST.copy() if request.method == "POST" else None
    fs_rot = RotSet(data, instance=precalc, prefix="rot")

    for form in fs_rot.forms:
        if hasattr(form.instance, 'setor') and form.instance.setor_id and not hasattr(form.instance, 'custo_hora'):
            form.instance.custo_hora = getattr(form.instance.setor, "custo_atual", 0)

    if request.method == "POST" and request.POST.get("form_roteiro_submitted") is not None:
            print("📥 RECEBIDO POST para aba roteiro")
            print("🔍 Dados POST:", dict(request.POST))
            print("🔍 Número de forms:", len(fs_rot.forms))

            if fs_rot.is_valid():
                print("✅ Formset Roteiro VÁLIDO")

                alguma_alteracao = False

                for i, form in enumerate(fs_rot.forms):
                    if not form.cleaned_data:
                        continue

                    obj = form.save(commit=False)

                    obj.precalculo = precalc
                    obj.usuario = request.user
                    obj.assinatura_nome = request.user.get_full_name() or request.user.username
                    obj.assinatura_cn = request.user.email
                    obj.data_assinatura = timezone.now()

                    try:
                        etapa_real = EtapaRoteiro.objects.filter(
                            etapa=obj.etapa,
                            roteiro=precalc.analise_comercial_item.roteiro_selecionado
                        ).first()

                        if etapa_real:
                            propriedades = PropriedadesEtapa.objects.filter(etapa=etapa_real).first()
                            if propriedades:
                                maquinas = propriedades.maquinas.all()
                                obj.maquinas_roteiro = ", ".join(m.codigo for m in maquinas)
                                obj.nome_acao = propriedades.nome_acao
                            else:
                                obj.maquinas_roteiro = ""
                                obj.nome_acao = ""
                        else:
                            obj.maquinas_roteiro = ""
                            obj.nome_acao = ""
                    except Exception as e:
                        print("⚠️ Erro ao buscar propriedades:", str(e))
                        obj.maquinas_roteiro = ""
                        obj.nome_acao = ""

                    obj.save()
                    alguma_alteracao = True
                    print("💾 Roteiro atualizado:", obj)


                if alguma_alteracao:
                    if form_precalculo and form_precalculo.is_valid():
                        campo_obs = "observacoes_roteiro"
                        valor = form_precalculo.cleaned_data.get(campo_obs)
                        setattr(precalc, campo_obs, valor)
                        precalc.save(update_fields=[campo_obs])
                    return True, fs_rot

                else:
                    messages.error(request, "Nenhuma alteração válida foi identificada para salvar.")
                    return False, fs_rot


            else:
                print("❌ Formset Roteiro INVÁLIDO")
                print(fs_rot.errors)



         

    return False, fs_rot