# email_cotacao_utils.py

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno
from alerts.models import AlertaConfigurado, AlertaUsuario


# -------------------------
# Utilitário: link público
# -------------------------
def gerar_link_publico(request, viewname: str, pk: int, tipo: str, dias_validade: int = 15) -> str:
    payload = {"id": int(pk), "tipo": tipo}
    token = signing.dumps(payload, salt="cotacao-publica")
    url = reverse(viewname, args=[pk])
    return request.build_absolute_uri(f"{url}?t={token}")


# ------------------------------------------------------
# Disparo (solicitação) de cotação de Matéria-Prima
# ------------------------------------------------------
def disparar_email_cotacao_material(request, material):
    """
    Envia e-mail para solicitar resposta de cotação da matéria-prima
    e cria alerta In-App para usuários/grupos configurados.
    """
    link_publico = gerar_link_publico(
        request,
        viewname="responder_cotacao_materia_prima",
        pk=material.pk,
        tipo="mp",
        dias_validade=15,
    )

    # Descrição da MP (se existir no catálogo)
    try:
        mp = MateriaPrimaCatalogo.objects.get(codigo=material.codigo)
        descricao = mp.descricao
    except MateriaPrimaCatalogo.DoesNotExist:
        descricao = "---"

    analise = getattr(material.precalculo, "analise_comercial_item", None)
    roteiro = getattr(analise, "roteiro_selecionado", None)
    fontes = roteiro.fontes_homologadas.all() if roteiro else []
    fontes_texto = "\n".join(f"• {f.nome}" for f in fontes) if fontes else "— Nenhuma fonte homologada definida —"

    corpo = f"""
🧪 Solicitação de Cotação - Matéria-Prima

📦 Código: {material.codigo}
📝 Descrição: {descricao}

🏭 Fontes Homologadas:
{fontes_texto}

🔗 Responder: {link_publico}
""".strip()

    # 1) E-mail oficial para Compras
    send_mail(
        subject="📨 Cotação de Matéria-Prima",
        message=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["compras@brasmol.com.br"],
        fail_silently=False,
    )

    # 2) Alerta In-App + (opcional) e-mails dos destinatários configurados
    try:
        config = AlertaConfigurado.objects.get(tipo="SOLICITACAO_COTACAO_MATERIAL", ativo=True)
        destinatarios = set(config.usuarios.all())
        for g in config.grupos.all():
            destinatarios.update(g.user_set.all())

        # Link do alerta → abrir diretamente a página de resposta
        try:
            link_resp = request.build_absolute_uri(reverse("responder_cotacao_materia_prima", args=[material.id]))
        except NoReverseMatch:
            link_resp = "/"

        for user in destinatarios:
            AlertaUsuario.objects.create(
                usuario=user,
                titulo=f"📨 Cotação de Material Solicitada ({material.codigo})",
                mensagem=f"Foi solicitada a cotação da matéria-prima {descricao}.",
                tipo="SOLICITACAO_COTACAO_MATERIAL",
                referencia_id=material.id,
                url_destino=link_resp,  # 🔗 vai direto ao template de resposta
            )

        # Replica por e-mail (se houver e-mails configurados)
        emails = [u.email for u in destinatarios if getattr(u, "email", None)]
        if emails:
            send_mail(
                subject="[Sistema Bras-Mol] Cotação de Matéria-Prima solicitada",
                message=corpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=True,
            )
    except AlertaConfigurado.DoesNotExist:
        pass

    # Carimbo de solicitação no(s) registro(s)
    if material.preco_kg is None and material.compras_solicitado_em is None:
        if material.status != "ok":
            material.status = "aguardando"
            material.compras_solicitado_em = timezone.now()
            material.save(update_fields=["status", "compras_solicitado_em"])


# ------------------------------------------------------
# View pública de resposta de cotação (Matéria-Prima)
# ------------------------------------------------------
def responder_cotacao_materia_prima(request, pk):
    """
    View pública para fornecedores responderem à cotação da matéria-prima.
    Para anônimos, valida o token assinado.
    """
    if not request.user.is_authenticated:
        token = request.GET.get("t")
        if not token:
            return HttpResponseForbidden("Acesso negado: link sem token.")
        try:
            data = signing.loads(token, salt="cotacao-publica", max_age=60 * 60 * 24 * 15)
            if int(data.get("id", 0)) != int(pk) or data.get("tipo") != "mp":
                return HttpResponseForbidden("Link inválido.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("Link expirado.")
        except signing.BadSignature:
            return HttpResponseForbidden("Link inválido.")

    material = get_object_or_404(PreCalculoMaterial, pk=pk)
    codigo = material.codigo

    materiais = (
        PreCalculoMaterial.objects
        .filter(precalculo=material.precalculo, codigo=codigo)
        .order_by("pk")
    )

    # Se todos já possuem preço, mostra a tela de finalizado
    if not materiais.filter(preco_kg__isnull=True).exists():
        return render(request, "cotacoes/cotacao_material_finalizada.html", {"material": material})

    fornecedores = (
        FornecedorQualificado.objects
        .filter(
            Q(ativo="Ativo"),
            Q(produto_servico__iregex=r"(arame\s+de\s+inox)|(arame\s+de\s+aço)|(fita\s+de\s+(aço|inox))")
        )
        .order_by("nome")
    )

    try:
        materia_prima = MateriaPrimaCatalogo.objects.get(codigo=codigo)
    except MateriaPrimaCatalogo.DoesNotExist:
        materia_prima = None

    cotacao_numero = material.precalculo.cotacao.numero if material.precalculo else None
    precalculo_numero = material.precalculo.numero if material.precalculo else None
    observacoes_gerais = material.precalculo.observacoes_materiais if material.precalculo else ""

    if request.method == "POST":
        houve_alteracao = False

        for i, mat in enumerate(materiais):
            # Se já está OK, não altera
            if mat.status == "ok":
                continue

            mat.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            mat.icms          = request.POST.get(f"icms_{i}") or None
            mat.lote_minimo   = request.POST.get(f"lote_minimo_{i}") or None
            mat.entrega_dias  = request.POST.get(f"entrega_dias_{i}") or None

            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
                try:
                    mat.preco_kg = Decimal(preco_raw)
                except (InvalidOperation, ValueError):
                    mat.preco_kg = None

            # Marca como OK se recebeu preço
            if mat.preco_kg:
                mat.status = "ok"

            mat.save()
            houve_alteracao = True

        if houve_alteracao:
            # Alerta + e-mail (padrão que você já usa) :contentReference[oaicite:2]{index=2}
            try:
                config = AlertaConfigurado.objects.get(tipo="RESPOSTA_COTACAO_MATERIAL", ativo=True)
                destinatarios = set(config.usuarios.all())
                for g in config.grupos.all():
                    destinatarios.update(g.user_set.all())

                for user in destinatarios:
                    AlertaUsuario.objects.create(
                        usuario=user,
                        titulo=f"📦 Cotação de Material Respondida ({material.codigo})",
                        mensagem=f"O fornecedor respondeu à cotação do material {material.codigo} – {materia_prima.descricao if materia_prima else ''}.",
                        tipo="RESPOSTA_COTACAO_MATERIAL",
                        referencia_id=material.id,
                        url_destino=request.path,
                    )

                emails = [u.email for u in destinatarios if getattr(u, "email", None)]
                if emails:
                    precalc = material.precalculo
                    # Link interno pro pré-cálculo
                    try:
                        if getattr(precalc, "cotacao_id", None):
                            link = request.build_absolute_uri(reverse("itens_precaculo", args=[precalc.cotacao_id]))
                        else:
                            link = request.build_absolute_uri(reverse("visualizar_precalculo", args=[precalc.id]))
                    except NoReverseMatch:
                        link = request.build_absolute_uri("/")

                    context = {
                        "usuario": request.user if request.user.is_authenticated else None,
                        "cotacao": getattr(precalc, "cotacao", None),
                        "precalculo": precalc,
                        "link": link,
                        "link_normas": None,
                        "qtd_normas": 0,
                    }

                    subject = f"[Sistema Bras-Mol] Cotação de Matéria-Prima respondida • PC {precalc.numero} • Cot {precalc.cotacao.numero if precalc and precalc.cotacao else '-'}"
                    html_body = render_to_string("emails/cotacao_material_respondida.html", context)
                    text_body = render_to_string("emails/cotacao_material_respondida.txt", context)

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=emails,
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send(fail_silently=True)

            except AlertaConfigurado.DoesNotExist:
                pass

            messages.success(request, "Cotações salvas com sucesso.")
            return render(request, "cotacoes/cotacao_material_finalizada.html", {"material": material})

        messages.info(request, "Nenhuma alteração foi enviada.")
        return redirect(request.path)

    # GET
    return render(
        request,
        "cotacoes/responder_cotacao_material.html",
        {
            "materiais": materiais,
            "fornecedores": fornecedores,
            "cotacao_numero": cotacao_numero,
            "precalculo_numero": precalculo_numero,
            "materia_prima": materia_prima,
            "observacoes_gerais": observacoes_gerais,
            "codigo": codigo,
        }
    )


# ------------------------------------------------------
# Disparo (solicitação) de cotação de Serviço Externo
# ------------------------------------------------------
def disparar_emails_cotacao_servicos(request, precalc):
    """
    Envia e-mail de solicitação de cotação por insumo e cria alerta In-App
    para usuários/grupos configurados, seguindo o mesmo padrão dos demais.
    """
    print(f"[SE-UTIL][INI][PC={precalc.id}]")
    pendentes = (
        precalc.servicos
        .select_related("insumo", "insumo__materia_prima")
        .filter(Q(preco_kg__isnull=True) | Q(preco_kg=0))
    )
    count = pendentes.count()
    ids = list(pendentes.values_list("id", flat=True))
    print(f"[SE-UTIL][PEND][PC={precalc.id}] count={count} ids={ids}")

    if count == 0:
        print(f"[SE-UTIL][PEND][PC={precalc.id}] vazio")
        return 0

    grupos = {}
    for s in pendentes:
        grupos.setdefault(s.insumo_id, []).append(s)

    enviados = 0

    for insumo_id, lista in grupos.items():
        s0 = lista[0]
        insumo = s0.insumo
        mp = getattr(insumo, "materia_prima", None)
        codigo = getattr(mp, "codigo", "sem_codigo")
        descricao = getattr(mp, "descricao", "-")

        # Link público para o fornecedor responder em lote
        try:
            link_publico = gerar_link_publico(
                request,
                viewname="responder_cotacao_servico_lote",
                pk=s0.pk,
                tipo="sev",
                dias_validade=15,
            )
        except NoReverseMatch as e:
            print(f"[SE-UTIL][URL][PC={precalc.id}] NoReverseMatch='{e}'")
            link_publico = "(rota indisponível)"

        corpo = f"""
🧪 Solicitação de Cotação - Serviço Externo

📦 Código: {codigo}
📝 Descrição: {descricao}

🔗 Responder: {link_publico}
""".strip()

        print(f"[SE-UTIL][MAIL][PC={precalc.id}] insumo_id={insumo_id} codigo={codigo} link={link_publico}")

        # 1) E-mail oficial para Compras
        send_mail(
            subject="📨 Cotação de Serviço Externo",
            message=corpo,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=["compras@brasmol.com.br"],
            fail_silently=False,
        )

        # 2) Alerta In-App + e-mail para os destinatários configurados
        try:
            config = AlertaConfigurado.objects.get(tipo="SOLICITACAO_COTACAO_SERVICO", ativo=True)
            destinatarios = set(config.usuarios.all())
            for g in config.grupos.all():
                destinatarios.update(g.user_set.all())

            # Link do alerta → abrir diretamente a página de resposta
            try:
                link_resp = request.build_absolute_uri(reverse("responder_cotacao_servico_lote", args=[s0.id]))
            except NoReverseMatch:
                link_resp = "/"

            for user in destinatarios:
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo=f"📨 Cotação de Serviço Solicitada ({codigo})",
                    mensagem=f"Foi solicitada a cotação do serviço externo referente ao material {codigo} – {descricao}.",
                    tipo="SOLICITACAO_COTACAO_SERVICO",
                    referencia_id=s0.id,
                    url_destino=link_resp,  # 🔗 vai direto ao template de resposta
                )

            emails = [u.email for u in destinatarios if getattr(u, "email", None)]
            if emails:
                send_mail(
                    subject="[Sistema Bras-Mol] Cotação de Serviço Externo solicitada",
                    message=corpo,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    recipient_list=emails,
                    fail_silently=True,
                )
        except AlertaConfigurado.DoesNotExist:
            pass

        # Carimbo de solicitação nos registros pendentes do insumo
        agora = timezone.now()
        ids_pend = [
            s.id for s in lista
            if (s.preco_kg is None or s.preco_kg == 0) and s.compras_solicitado_em is None
        ]
        if ids_pend:
            updated = PreCalculoServicoExterno.objects.filter(id__in=ids_pend).update(
                status="aguardando",
                compras_solicitado_em=agora
            )
            print(f"[SE-UTIL][UPD][PC={precalc.id}] carimbados={updated} ids={ids_pend}")

        enviados += 1

    print(f"[SE-UTIL][END][PC={precalc.id}] enviados_por_insumo={enviados}")
    return enviados


# ------------------------------------------------------
# View pública de resposta de cotação (Serviço em lote)
# ------------------------------------------------------
def responder_cotacao_servico_lote(request, pk):
    """
    View pública para fornecedores responderem à cotação de serviços (em lote).
    Para anônimos, valida o token assinado.
    """
    if not request.user.is_authenticated:
        token = request.GET.get("t")
        if not token:
            return HttpResponseForbidden("Acesso negado: link sem token.")
        try:
            data = signing.loads(token, salt="cotacao-publica", max_age=60 * 60 * 24 * 15)
            if int(data.get("id", 0)) != int(pk) or data.get("tipo") != "sev":
                return HttpResponseForbidden("Link inválido.")
        except signing.SignatureExpired:
            return HttpResponseForbidden("Link expirado.")
        except signing.BadSignature:
            return HttpResponseForbidden("Link inválido.")

    servico = get_object_or_404(PreCalculoServicoExterno, pk=pk)
    codigo = servico.insumo.materia_prima.codigo

    servicos = (
        PreCalculoServicoExterno.objects
        .filter(precalculo=servico.precalculo, insumo__materia_prima__codigo=codigo)
        .select_related("insumo", "insumo__materia_prima")
        .order_by("pk")
    )

    # Se todos já possuem preço, mostra a tela de finalizado
    if not servicos.filter(preco_kg__isnull=True).exists():
        return render(request, "cotacoes/cotacao_servico_lote_finalizada.html", {"servico": servico})

    fornecedores = (
        FornecedorQualificado.objects
        .filter(
            Q(status__in=["Qualificado", "Qualificado Condicional"]),
            Q(produto_servico__iregex=r"(trat)")
        )
        .order_by("nome")
    )

    try:
        materia_prima = servico.insumo.materia_prima
    except Exception:
        materia_prima = None

    cotacao_numero     = servico.precalculo.cotacao.numero if servico.precalculo else None
    precalculo_numero  = servico.precalculo.numero if servico.precalculo else None
    observacoes_gerais = servico.precalculo.observacoes_servicos if servico.precalculo else ""

    if request.method == "POST":
        houve_alteracao = False

        # Template deve enviar <input type="hidden" name="id_{{ forloop.counter0 }}" value="{{ sev.id }}">
        for i, _ in enumerate(servicos):
            sev_id = request.POST.get(f"id_{i}")
            if not sev_id:
                continue

            try:
                sev = PreCalculoServicoExterno.objects.get(id=sev_id)
            except PreCalculoServicoExterno.DoesNotExist:
                continue

            sev.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None

            # Normalizador local pt-BR → Decimal
            def _dec(v, casas="0.01"):
                if v in (None, ""):
                    return None
                s = str(v).strip().replace(" ", "")
                try:
                    if "," in s and "." in s:
                        # pt-BR: 1.234,56 → remove milhares "." e troca "," por "."
                        if s.rfind(",") > s.rfind("."):
                            s = s.replace(".", "").replace(",", ".")
                        else:
                            # en-US 1,234.56 → remove vírgulas de milhar
                            s = s.replace(",", "")
                    elif "," in s:
                        s = s.replace(",", ".")
                    return Decimal(s).quantize(Decimal(casas))
                except (InvalidOperation, ValueError):
                    return None

            sev.icms         = _dec(request.POST.get(f"icms_{i}"), "0.01")
            sev.lote_minimo  = _dec(request.POST.get(f"lote_minimo_{i}"), "0.01")

            entrega_raw      = request.POST.get(f"entrega_dias_{i}")
            sev.entrega_dias = int(entrega_raw) if (entrega_raw and entrega_raw.isdigit()) else None

            sev.preco_kg     = _dec(request.POST.get(f"preco_kg_{i}"), "0.0001")

            # Marca como OK apenas se houver preço informado
            if sev.preco_kg:
                sev.status = "ok"

            sev.save()
            houve_alteracao = True

        if houve_alteracao:
            # Alerta + e-mail (padrão que você já usa) :contentReference[oaicite:3]{index=3}
            try:
                config = AlertaConfigurado.objects.get(tipo="RESPOSTA_COTACAO_SERVICO", ativo=True)
                destinatarios = set(config.usuarios.all())
                for g in config.grupos.all():
                    destinatarios.update(g.user_set.all())

                mp = getattr(servico.insumo, "materia_prima", None)
                codigo_mp = getattr(mp, "codigo", "")
                desc_mp   = getattr(mp, "descricao", "")

                for user in destinatarios:
                    AlertaUsuario.objects.create(
                        usuario=user,
                        titulo=f"🛠 Cotação de Serviço Respondida ({codigo_mp})",
                        mensagem=f"O fornecedor respondeu à cotação do serviço referente ao material {codigo_mp} – {desc_mp}.",
                        tipo="RESPOSTA_COTACAO_SERVICO",
                        referencia_id=servico.id,
                        url_destino=request.path,
                    )

                emails = [u.email for u in destinatarios if getattr(u, "email", None)]
                if emails:
                    precalc = servico.precalculo
                    try:
                        if getattr(precalc, "cotacao_id", None):
                            link = request.build_absolute_uri(reverse("itens_precaculo", args=[precalc.cotacao_id]))
                        else:
                            link = request.build_absolute_uri(reverse("visualizar_precalculo", args=[precalc.id]))
                    except NoReverseMatch:
                        link = request.build_absolute_uri("/")

                    context = {
                        "usuario": request.user if request.user.is_authenticated else None,
                        "cotacao": getattr(precalc, "cotacao", None),
                        "precalculo": precalc,
                        "link": link,
                        "codigo_mp": codigo_mp,
                        "desc_mp": desc_mp,
                        "link_normas": None,
                        "qtd_normas": 0,
                    }

                    subject = f"[Sistema Bras-Mol] Cotação de Serviço respondida • PC {precalc.numero} • Cot {precalc.cotacao.numero if precalc and precalc.cotacao else '-'}"
                    html_body = render_to_string("emails/cotacao_servico_respondida.html", context)
                    text_body = render_to_string("emails/cotacao_servico_respondida.txt", context)

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=emails,
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send(fail_silently=True)

            except AlertaConfigurado.DoesNotExist:
                pass

            messages.success(request, "Cotações salvas com sucesso.")
            return render(request, "cotacoes/cotacao_servico_lote_finalizada.html", {"servico": servico})

        messages.info(request, "Nenhuma alteração foi enviada.")
        return redirect(request.path)

    # GET
    return render(
        request,
        "cotacoes/responder_cotacao_servico_lote.html",
        {
            "servicos": servicos,
            "fornecedores": fornecedores,
            "cotacao_numero": cotacao_numero,
            "precalculo_numero": precalculo_numero,
            "materia_prima": materia_prima,
            "observacoes_gerais": observacoes_gerais,
            "codigo": codigo,
        }
    )
