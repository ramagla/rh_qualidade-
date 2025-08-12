# C:\Projetos\RH-Qualidade\rh_qualidade\comercial\views\handlers\roteiro_handler.py
from decimal import Decimal
from django.forms import inlineformset_factory
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from comercial.forms.precalculos_form import RoteiroCotacaoForm
from comercial.models.precalculo import PreCalculo, RoteiroCotacao
from tecnico.models.roteiro import EtapaRoteiro, PropriedadesEtapa
from alerts.models import AlertaConfigurado, AlertaUsuario


def _coletar_destinatarios(tipo_alerta: str):
    emails = []
    usuarios_in_app = set()
    cfg = AlertaConfigurado.objects.filter(tipo=tipo_alerta, ativo=True).first()
    if not cfg:
        return emails, usuarios_in_app

    for u in cfg.usuarios.all():
        if u.email:
            emails.append(u.email)
        usuarios_in_app.add(u)

    for g in cfg.grupos.all():
        for u in g.user_set.all():
            if u.email:
                emails.append(u.email)
            usuarios_in_app.add(u)

    # remover duplicados preservando ordem
    emails = list(dict.fromkeys(emails))
    return emails, usuarios_in_app


def _montar_links(request, precalc: PreCalculo):
    try:
        destino = reverse("editar_precaculo", args=[precalc.pk]) + "?aba=precofinal"
    except Exception:
        destino = reverse("itens_precaculo", args=[precalc.cotacao.pk])

    login_com_next = f"{reverse('login')}?{urlencode({'next': destino})}"
    link = request.build_absolute_uri(login_com_next)

    link_normas_abs = None
    qtd_normas = 0
    try:
        from comercial.models.clientes import ClienteDocumento
        normas_qs = ClienteDocumento.objects.filter(
            cliente=precalc.cotacao.cliente, tipo__in=["Norma", "Normas"]
        ).order_by("-data_upload")
        qtd_normas = normas_qs.count()
        if qtd_normas > 0:
            try:
                normas_path = reverse("cliente_documentos", args=[precalc.cotacao.cliente.pk]) + "?tipo=Norma"
                normas_next = f"{reverse('login')}?{urlencode({'next': normas_path})}"
                link_normas_abs = request.build_absolute_uri(normas_next)
            except Exception:
                primeiro_arquivo = normas_qs.first().arquivo.url
                link_normas_abs = request.build_absolute_uri(primeiro_arquivo)
    except Exception:
        link_normas_abs = None
        qtd_normas = 0

    return destino, link, link_normas_abs, qtd_normas


def notificar_roteiro_atualizado(request, precalc: PreCalculo):
    emails, usuarios_in_app = _coletar_destinatarios("ROTEIRO_ATUALIZADO")
    destino, link, link_normas_abs, qtd_normas = _montar_links(request, precalc)

    ctx = {
        "usuario": request.user,
        "cotacao": precalc.cotacao,
        "precalculo": precalc,
        "link": link,
        "link_normas": link_normas_abs,
        "qtd_normas": qtd_normas,
    }

    # 1) Render dos templates + logs
    try:
        subject = render_to_string("alertas/roteiro_atualizado_assunto.txt", ctx).strip()
        text    = render_to_string("alertas/roteiro_atualizado.txt", ctx)
        html    = render_to_string("alertas/roteiro_atualizado.html", ctx)
        print("🧪 [ROTEIRO_NOTIFY] subject:", subject)
    except Exception as e:
        print("❌ [ROTEIRO_NOTIFY] erro render templates:", e)
        raise

    # 2) Diagnóstico de destinatários
    print("🧪 [ROTEIRO_NOTIFY] destinatários (antes):", emails)

    # (Opcional) Fallback em DEBUG: se não houver e-mails configurados em AlertaConfigurado,
    # envia para o superuser com e-mail definido só para validar o envio em ambiente dev.
    if not emails and getattr(settings, "DEBUG", False):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            debug_emails = list(User.objects.filter(is_superuser=True).exclude(email="").values_list("email", flat=True))
            if debug_emails:
                emails = debug_emails
                print("⚠️ [ROTEIRO_NOTIFY] usando fallback DEBUG para:", emails)
        except Exception as e:
            print("⚠️ [ROTEIRO_NOTIFY] fallback DEBUG falhou:", e)

    # 3) Validação de 'from' e backend
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@brasmol.com.br"
    print("🧪 [ROTEIRO_NOTIFY] EMAIL_BACKEND:", getattr(settings, "EMAIL_BACKEND", None))
    print("🧪 [ROTEIRO_NOTIFY] DEFAULT_FROM_EMAIL:", from_email)

    # 4) Envio
    if emails:
        try:
            msg = EmailMultiAlternatives(subject, text, from_email, emails)
            msg.attach_alternative(html, "text/html")
            sent = msg.send(fail_silently=False)
            print(f"✅ [ROTEIRO_NOTIFY] email enviado. count={sent} para={emails}")
        except Exception as e:
            print("❌ [ROTEIRO_NOTIFY] erro SMTP:", e)
            raise
    else:
        print("⚠️ [ROTEIRO_NOTIFY] nenhum destinatário configurado. Sem envio.")


    for u in usuarios_in_app:
        AlertaUsuario.objects.create(
            usuario=u,
            titulo=subject,
            mensagem=text,
            tipo="ROTEIRO_ATUALIZADO",
            referencia_id=precalc.id,
            url_destino=destino,
        )


def processar_aba_roteiro(request, precalc, form_precalculo=None):
    roteiro_atual = list(precalc.roteiro_item.values_list('etapa', flat=True))

    roteiro_novo = []
    if getattr(precalc, "analise_comercial_item", None):
        roteiro = getattr(precalc.analise_comercial_item, "roteiro_selecionado", None)

        if roteiro:
            roteiro_novo = list(roteiro.etapas.values_list('etapa', flat=True))

            if roteiro_novo != roteiro_atual:
                with transaction.atomic():
                    precalc.roteiro_item.all().delete()

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
            'maquinas_roteiro',
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

            for form in fs_rot.forms:
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
