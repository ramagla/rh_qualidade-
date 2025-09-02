from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from comercial.forms.viabilidade_forms import ViabilidadeAnaliseRiscoForm
from comercial.models import Cliente, PreCalculo
from comercial.models.viabilidade import ViabilidadeAnaliseRisco

# ➕ alertas (in-app + e-mail)
from alerts.models import AlertaConfigurado, AlertaUsuario
from alerts.tasks import send_email_async
from django.conf import settings

@login_required
@permission_required("comercial.view_viabilidadeanaliserisco", raise_exception=True)
def lista_viabilidades(request):
    viabilidades = ViabilidadeAnaliseRisco.objects.select_related("precalculo__cotacao", "cliente")

    # Filtros
    data_de = request.GET.get("data_criacao_de")
    data_ate = request.GET.get("data_criacao_ate")
    cliente_id = request.GET.get("cliente")

    if data_de:
        try:
            data_inicio = make_aware(datetime.strptime(data_de, "%Y-%m-%d"))
            viabilidades = viabilidades.filter(criado_em__gte=data_inicio)
        except Exception:
            pass

    if data_ate:
        try:
            data_fim = make_aware(datetime.strptime(data_de, "%Y-%m-%d"))
            viabilidades = viabilidades.filter(criado_em__lte=data_fim)
        except Exception:
            pass

    if cliente_id:
        viabilidades = viabilidades.filter(cliente_id=cliente_id)

    # Ordenação e paginação
    viabilidades = viabilidades.order_by("-numero")
    paginator = Paginator(viabilidades, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Indicadores (exemplo)
    total_viabilidades = viabilidades.count()
    total_aprovadas = viabilidades.filter(conclusao_tecnica="viavel").count()
    total_inviaveis = viabilidades.filter(conclusao_tecnica="inviavel").count()
    total_comercial_assinada = viabilidades.exclude(assinatura_comercial_nome__isnull=True).count()

    context = {
        "page_obj": page_obj,
        "clientes": Cliente.objects.all(),
        "total_viabilidades": total_viabilidades,
        "total_aprovadas": total_aprovadas,
        "total_inviaveis": total_inviaveis,
        "total_comercial_assinada": total_comercial_assinada,
    }

    return render(request, "viabilidade/lista_viabilidades.html", context)



# viabilidade_views.py

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.conf import settings  # ➕ (para montar link absoluto no e-mail, se quiser)

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from comercial.forms.viabilidade_forms import ViabilidadeAnaliseRiscoForm
from comercial.models import Cliente, PreCalculo
from comercial.models.viabilidade import ViabilidadeAnaliseRisco

# ➕ ALERTAS (in-app + e-mail)
from alerts.models import AlertaConfigurado, AlertaUsuario
from alerts.tasks import send_email_async


@login_required
@permission_required("comercial.add_viabilidadeanaliserisco", raise_exception=True)
def cadastrar_viabilidade(request):
    aba = request.POST.get("aba") or "comercial"
    print("📥 [CADASTRAR] POST recebido")
    print("🧭 Aba recebida:", aba)
    print("📦 Dados brutos:", request.POST.dict())

    form = ViabilidadeAnaliseRiscoForm(request.POST or None)

    CAMPOS_ABA = {
        "comercial": [
            "precalculo", "cliente", "codigo_desenho",
            "produto_definido", "risco_comercial", "conclusao_comercial", "consideracoes_comercial",
        ],
        "custos": [
            "capacidade_fabricacao", "custo_transformacao", "custo_ferramental",
            "metodo_alternativo", "risco_logistico",
            "conclusao_custos", "consideracoes_custos",
        ],
        "tecnica": [
            "recursos_suficientes", "atende_especificacoes", "atende_tolerancias",
            "capacidade_processo", "permite_manuseio", "precisa_cep", "cep_usado_similares",
            "processos_estaveis", "capabilidade_ok", "atende_requisito_cliente", "risco_tecnico",
            "conclusao_tecnica", "consideracoes_tecnicas",
        ],
    }

    # Cadastro inicial só permite a aba "comercial" (mesma regra já existente)
    if request.method == "POST" and aba != "comercial":
        messages.warning(
            request,
            "Para iniciar o cadastro, salve primeiro a aba Comercial. Em seguida, edite para preencher Custos e Técnica."
        )
        print("⚠️ [CADASTRAR] Tentativa de salvar aba diferente de 'comercial' no cadastro inicial.")
        return render(request, "viabilidade/form_viabilidade_analise_risco.html", {
            "form": form,
            "titulo": "Cadastrar Viabilidade / Análise de Risco",
            "viabilidade": None,
            "item": None,
        })

    if request.method == "POST":
        # Restringe os fields visíveis/enviáveis pela aba ativa (como já fazia)
        campos_permitidos = set(CAMPOS_ABA.get(aba, []))
        for name in list(form.fields.keys()):
            if name not in campos_permitidos:
                del form.fields[name]

        if form.is_valid():
            print("✅ [CADASTRAR] Formulário VÁLIDO (aba:", aba, ")")

            viab = form.save(commit=False)
            viab.criado_por = request.user

            # Assinatura comercial (mantido)
            viab.assinatura_comercial_nome = request.user.get_full_name()
            viab.assinatura_comercial_departamento = (
                getattr(getattr(request.user, "funcionario", None), "cargo_atual", None).nome
                if hasattr(request.user, "funcionario") and getattr(request.user.funcionario, "cargo_atual", None)
                else ""
            )
            viab.assinatura_comercial_data = timezone.now()
            viab.save()
            print("💾 [CADASTRAR] Viabilidade criada com ID:", viab.pk)

            # Assinatura eletrônica (mantido)
            hash_valido = gerar_assinatura(viab, request.user)
            conteudo_assinado = f"COMERCIAL|{viab.pk}|{viab.conclusao_comercial}"

            AssinaturaEletronica.objects.get_or_create(
                hash=hash_valido,
                defaults={
                    "conteudo": conteudo_assinado,
                    "usuario": request.user,
                    "origem_model": "ViabilidadeAnaliseRisco",
                    "origem_id": viab.pk,
                }
            )

            # 🔔 ALERTA in-app + MODAL (conforme configuração) + E-MAIL
            try:
                config = AlertaConfigurado.objects.get(
                    tipo="VIABILIDADE_CRIADA",  # ➕ adicione este tipo em TIPO_ALERTA_CHOICES
                    ativo=True
                )
                exigir_modal = bool(getattr(config, "exigir_confirmacao_modal", False))
                destinatarios = set(config.usuarios.all())
                for g in config.grupos.all():
                    destinatarios.update(g.user_set.all())
            except AlertaConfigurado.DoesNotExist:
                exigir_modal = False
                destinatarios = set()

            url_destino = reverse("visualizar_viabilidade", args=[viab.pk])  # rota existente
            base = getattr(settings, "SITE_URL", "").rstrip("/")
            link_abs = f"{base}{url_destino}" if base else url_destino

            titulo = f"🆕 Nova Viabilidade Nº {viab.numero:03d}"
            corpo = (
                "Foi cadastrada uma nova Viabilidade / Análise de Risco.\n"
                f"Cliente: {getattr(viab, 'cliente', '—')}\n"
                f"Acesse: {link_abs}"
            )

            for user in destinatarios:
                # In-app (modal se configurado)
                AlertaUsuario.objects.create(
                    usuario=user,
                    titulo=titulo,
                    mensagem=corpo,
                    tipo="VIABILIDADE_CRIADA",
                    referencia_id=viab.pk,
                    url_destino=url_destino,          # relativo (frontend resolve)
                    exige_confirmacao=exigir_modal
                )
                # E-mail (assíncrono)
                if user.email:
                    send_email_async.delay(
                        subject=titulo,
                        message=corpo,
                        recipient_list=[user.email],
                    )

            messages.success(request, "Aba 'comercial' salva com sucesso. Continue preenchendo as demais abas.")
            return redirect("editar_viabilidade", pk=viab.pk)
        else:
            print("❌ [CADASTRAR] Formulário INVÁLIDO (aba:", aba, ")")
            print("🧾 Erros:", form.errors)

    return render(request, "viabilidade/form_viabilidade_analise_risco.html", {
        "form": form,
        "titulo": "Cadastrar Viabilidade / Análise de Risco",
        "viabilidade": None,
        "item": None,
    })



@login_required
@permission_required("comercial.change_viabilidadeanaliserisco", raise_exception=True)
def editar_viabilidade(request, pk):
    viabilidade = get_object_or_404(ViabilidadeAnaliseRisco, pk=pk)
    item = getattr(viabilidade.precalculo, "item", None)
    aba = request.POST.get("aba") if request.method == "POST" else "comercial"

    print("📥 [EDITAR] POST recebido" if request.method == "POST" else "👁️ [EDITAR] GET")
    print("🧭 Aba ativa:", aba)
    if request.method == "POST":
        print("📦 Dados brutos:", request.POST.dict())

    CAMPOS_ABA = {
        "comercial": [
            "precalculo", "cliente", "codigo_desenho",
            "produto_definido", "risco_comercial", "conclusao_comercial", "consideracoes_comercial",
        ],
        "custos": [
            "capacidade_fabricacao", "custo_transformacao", "custo_ferramental",
            "metodo_alternativo", "risco_logistico",
            "conclusao_custos", "consideracoes_custos",
        ],
        "tecnica": [
            "recursos_suficientes", "atende_especificacoes", "atende_tolerancias",
            "capacidade_processo", "permite_manuseio", "precisa_cep", "cep_usado_similares",
            "processos_estaveis", "capabilidade_ok", "atende_requisito_cliente", "risco_tecnico",
            "conclusao_tecnica", "consideracoes_tecnicas",
        ],
    }

    if request.method == "POST":
        form = ViabilidadeAnaliseRiscoForm(request.POST, instance=viabilidade)

        campos_permitidos = set(CAMPOS_ABA.get(aba, []))
        for name in list(form.fields.keys()):
            if name not in campos_permitidos:
                del form.fields[name]

        if form.is_valid():
            instancia = form.save(commit=False)

            if aba == "comercial":
                instancia.assinatura_comercial_nome = request.user.get_full_name()
                instancia.assinatura_comercial_departamento = (
                    getattr(getattr(request.user, "funcionario", None), "cargo_atual", None).nome
                    if hasattr(request.user, "funcionario") and getattr(request.user.funcionario, "cargo_atual", None)
                    else ""
                )
                instancia.assinatura_comercial_data = timezone.now()

                instancia.save()
                hash_valido = gerar_assinatura(instancia, request.user)
                conteudo = f"COMERCIAL|{instancia.pk}|{instancia.conclusao_comercial}"

            elif aba == "custos":
                instancia.responsavel_custos = request.user.get_full_name()
                instancia.departamento_custos = (
                    getattr(getattr(request.user, "funcionario", None), "cargo_atual", None).nome
                    if hasattr(request.user, "funcionario") and getattr(request.user.funcionario, "cargo_atual", None)
                    else ""
                )
                instancia.data_custos = timezone.now()

                instancia.save()
                hash_valido = gerar_assinatura(instancia, request.user)
                conteudo = f"CUSTOS|{instancia.pk}|{instancia.conclusao_custos}"

            elif aba == "tecnica":
                instancia.responsavel_tecnica = request.user.get_full_name()
                instancia.departamento_tecnica = (
                    getattr(getattr(request.user, "funcionario", None), "cargo_atual", None).nome
                    if hasattr(request.user, "funcionario") and getattr(request.user.funcionario, "cargo_atual", None)
                    else ""
                )
                instancia.data_tecnica = timezone.now()

                instancia.save()
                hash_valido = gerar_assinatura(instancia, request.user)
                conteudo = f"TECNICA|{instancia.pk}|{instancia.conclusao_tecnica}"

            # Salva assinatura eletrônica
            AssinaturaEletronica.objects.get_or_create(
                hash=hash_valido,
                defaults={
                    "conteudo": conteudo,
                    "usuario": request.user,
                    "origem_model": "ViabilidadeAnaliseRisco",
                    "origem_id": instancia.pk,
                }
            )

            print(f"💾 [EDITAR] Aba '{aba}' salva com sucesso para a Viabilidade ID {instancia.pk}.")
            messages.success(request, f"Aba '{aba}' salva com sucesso.")
            return redirect("editar_viabilidade", pk=viabilidade.pk)
        else:
            print("❌ [EDITAR] Formulário INVÁLIDO (aba:", aba, ")")
            print("🧾 Erros:", form.errors)
    else:
        form = ViabilidadeAnaliseRiscoForm(instance=viabilidade)

    return render(request, "viabilidade/form_viabilidade_analise_risco.html", {
        "form": form,
        "titulo": f"Editar Viabilidade Nº {viabilidade.numero:03d}",
        "viabilidade": viabilidade,
        "item": item,
    })


@login_required
@permission_required("comercial.view_viabilidadeanaliserisco", raise_exception=True)
def visualizar_viabilidade(request, pk):
    viabilidade = get_object_or_404(
        ViabilidadeAnaliseRisco.objects.select_related("precalculo__cotacao"),
        pk=pk
    )

    cotacao = getattr(viabilidade.precalculo, "cotacao", None)
    cotacao_numero = cotacao.numero if cotacao else None
    precalculo_numero = getattr(viabilidade.precalculo, "numero", None)

    # Busca as assinaturas eletrônicas de cada aba e gera o QR Code

    assinaturas_qr = {}
    for aba in ["comercial", "custos", "tecnica"]:
        try:
            assinatura = (
                AssinaturaEletronica.objects
                .filter(
                    origem_model="ViabilidadeAnaliseRisco",
                    origem_id=viabilidade.pk,
                    conteudo__icontains=aba.upper()
                )
                .latest("data_assinatura")
            )

            assinaturas_qr[aba] = {
                "nome": assinatura.usuario.get_full_name(),
                "departamento": getattr(
                    getattr(assinatura.usuario, "funcionario", None),
                    "cargo_atual", None
                ).nome if hasattr(assinatura.usuario, "funcionario") else "",
                "email": assinatura.usuario.email,
                "data": assinatura.data_assinatura,
                "hash": assinatura.hash,
                "qr": gerar_qrcode_base64(
                    request.build_absolute_uri(
                        reverse("validar_assinatura", args=[assinatura.hash])
                    )
                )

            }
        except ObjectDoesNotExist:
            assinaturas_qr[aba] = None


    return render(request, "viabilidade/visualizar_f106.html", {
        "titulo": f"F106 - Viabilidade / Análise de Risco Nº {viabilidade.numero:03d}",
        "viabilidade": viabilidade,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "assinaturas_qr": assinaturas_qr,
    })



@login_required
@permission_required("comercial.delete_viabilidadeanaliserisco", raise_exception=True)
def excluir_viabilidade(request, pk):
    viabilidade = get_object_or_404(ViabilidadeAnaliseRisco, pk=pk)
    if request.method == "POST":
        viabilidade.delete()
        return redirect("lista_viabilidades")

    return render(request, "partials/global/_modal_exclusao.html", {
        "objeto": viabilidade,
        "url_exclusao": "excluir_viabilidade",
        "titulo": "Excluir Viabilidade / Análise de Risco"
    })
