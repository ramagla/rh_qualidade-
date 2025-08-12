from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse, NoReverseMatch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core import signing
from django.utils import timezone

from qualidade_fornecimento.models.fornecedor import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno
from Funcionario.models import Settings as SistemaSettings
from alerts.models import AlertaConfigurado, AlertaUsuario


def gerar_link_publico(request, viewname: str, pk: int, tipo: str, dias_validade: int = 15) -> str:
    payload = {"id": int(pk), "tipo": tipo}
    token = signing.dumps(payload, salt="cotacao-publica")
    url = reverse(viewname, args=[pk])
    return request.build_absolute_uri(f"{url}?t={token}")

def disparar_email_cotacao_material(request, material):
    """
    Envia e-mail para solicitar resposta de cotação da matéria-prima.
    """
    link = gerar_link_publico(
        request,
        viewname="responder_cotacao_materia_prima",
        pk=material.pk,
        tipo="mp",
        dias_validade=15
    )

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

🔗 Responder: {link}
"""

    send_mail(
        subject="📨 Cotação de Matéria-Prima",
        message=corpo.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["compras@brasmol.com.br"],
        fail_silently=False,
    )

    if material.preco_kg is None and material.compras_solicitado_em is None:
        if material.status != "ok":
            material.status = "aguardando"
            material.compras_solicitado_em = timezone.now()
            material.save(update_fields=["status", "compras_solicitado_em"])

        else:
            # já "ok": não altera nada
            pass

from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from qualidade_fornecimento.models import FornecedorQualificado
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo
from comercial.models.precalculo import PreCalculoMaterial, PreCalculoServicoExterno

def responder_cotacao_materia_prima(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação da matéria-prima.
    Para usuários anônimos, exige validação do token (link assinado).
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

            # Opcional: marca como OK se recebeu preço
            if mat.preco_kg:
                mat.status = "ok"

            mat.save()
            houve_alteracao = True

        if houve_alteracao:
            # Alerta + e-mail apenas uma vez após processar todas as linhas
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
                    # Tenta gerar link interno pro pré-cálculo
                    try:
                        if getattr(precalc, "cotacao_id", None):
                            link = request.build_absolute_uri(
                                reverse("itens_precaculo", args=[precalc.cotacao_id])
                            )
                        else:
                            link = request.build_absolute_uri(
                                reverse("visualizar_precalculo", args=[precalc.id])
                            )
                    except NoReverseMatch:
                        link = request.build_absolute_uri("/")


                    context = {
                        "usuario": request.user if request.user.is_authenticated else None,
                        "cotacao": getattr(precalc, "cotacao", None),
                        "precalculo": precalc,
                        "link": link,
                        # opcionais para manter padrão do seu modelo
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




from django.db.models import Q
from django.urls import NoReverseMatch

from django.urls import reverse
from django.conf import settings

from django.db.models import Q
from django.urls import NoReverseMatch
from django.utils import timezone
from django.conf import settings

def disparar_emails_cotacao_servicos(request, precalc):
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

        try:
            link = gerar_link_publico(
                request,
                viewname="responder_cotacao_servico_lote",
                pk=s0.pk,
                tipo="sev",
                dias_validade=15
            )
        except NoReverseMatch as e:
            print(f"[SE-UTIL][URL][PC={precalc.id}] NoReverseMatch='{e}'")
            link = "(rota indisponível)"

        corpo = f"""
🧪 Solicitação de Cotação - Serviço Externo

📦 Código: {codigo}
📝 Descrição: {descricao}

🔗 Responder: {link}
""".strip()

        print(f"[SE-UTIL][MAIL][PC={precalc.id}] insumo_id={insumo_id} codigo={codigo} link={link}")
        send_mail(
            subject="📨 Cotação de Serviço Externo",
            message=corpo,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=["compras@brasmol.com.br"],
            fail_silently=False,
        )

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




from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from qualidade_fornecimento.models import FornecedorQualificado
from comercial.models.precalculo import PreCalculoServicoExterno
from qualidade_fornecimento.models.materiaPrima_catalogo import MateriaPrimaCatalogo

def responder_cotacao_servico_lote(request, pk):
    """
    View pública para que fornecedores preencham os dados de cotação de serviços em lote.
    Para usuários anônimos, exige validação do token (link assinado).
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

        # Importante: o template deve enviar <input type="hidden" name="id_{{ forloop.counter0 }}" value="{{ sev.id }}">
        for i, _ in enumerate(servicos):
            sev_id = request.POST.get(f"id_{i}")
            if not sev_id:
                continue

            try:
                sev = PreCalculoServicoExterno.objects.get(id=sev_id)
            except PreCalculoServicoExterno.DoesNotExist:
                continue

            sev.fornecedor_id = request.POST.get(f"fornecedor_{i}") or None
            sev.icms          = request.POST.get(f"icms_{i}") or None
            sev.lote_minimo   = request.POST.get(f"lote_minimo_{i}") or None
            sev.entrega_dias  = request.POST.get(f"entrega_dias_{i}") or None

            preco_raw = request.POST.get(f"preco_kg_{i}") or None
            if preco_raw:
                preco_raw = preco_raw.replace(",", ".")
                try:
                    sev.preco_kg = Decimal(preco_raw)
                except (InvalidOperation, ValueError):
                    sev.preco_kg = None

            # Marca como OK apenas se houver preço informado
            if sev.preco_kg:
                sev.status = "ok"

            sev.save()
            houve_alteracao = True

        if houve_alteracao:
            # Alerta + e-mail enviados uma única vez após processar todas as linhas
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
                            link = request.build_absolute_uri(
                                reverse("itens_precaculo", args=[precalc.cotacao_id])
                            )
                        else:
                            link = request.build_absolute_uri(
                                reverse("visualizar_precalculo", args=[precalc.id])
                            )
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



