from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from comercial.forms.ordem_desenvolvimento_form import OrdemDesenvolvimentoForm
from comercial.models import OrdemDesenvolvimento, Cliente
from alerts.models import AlertaConfigurado, AlertaUsuario
from django.conf import settings
from alerts.tasks import send_email_async

@login_required
@permission_required("comercial.view_ordemdesenvolvimento", raise_exception=True)
def lista_ordens_desenvolvimento(request):
    ordens = OrdemDesenvolvimento.objects.select_related("item", "cliente").all()

    # Filtros
    data_de = request.GET.get("data_criacao_de")
    data_ate = request.GET.get("data_criacao_ate")
    cliente_id = request.GET.get("cliente")
    razao = request.GET.get("razao")
    oem = request.GET.get("oem")
    metodologia = request.GET.get("metodologia")

    if data_de:
        try:
            data_inicio = make_aware(datetime.strptime(data_de, "%Y-%m-%d"))
            ordens = ordens.filter(created_at__gte=data_inicio)
        except:
            pass

    if data_ate:
        try:
            data_fim = make_aware(datetime.strptime(data_ate, "%Y-%m-%d"))
            ordens = ordens.filter(created_at__lte=data_fim)
        except:
            pass

    if cliente_id:
        ordens = ordens.filter(cliente_id=cliente_id)

    if razao:
        ordens = ordens.filter(razao=razao)

    if oem in ["0", "1"]:
        ordens = ordens.filter(automotivo_oem=bool(int(oem)))

    if metodologia:
        ordens = ordens.filter(metodologia_aprovacao__icontains=metodologia)

    # Ordenação
    ordens = ordens.order_by("-numero")

    # Paginação
    paginator = Paginator(ordens, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Indicadores
    total_ordens = ordens.count()
    total_com_amostra = ordens.exclude(qtde_amostra__isnull=True).count()
    total_com_ferramenta = ordens.filter(ferramenta="sim").count()
    total_com_prazo = ordens.exclude(prazo_solicitado__isnull=True).count()

    context = {
        "page_obj": page_obj,
        "total_ordens": total_ordens,
        "total_com_amostra": total_com_amostra,
        "total_com_ferramenta": total_com_ferramenta,
        "total_com_prazo": total_com_prazo,
        "clientes": Cliente.objects.all(),
        "ordem_model": OrdemDesenvolvimento,  # usado no template para acessar RAZOES
        "metodologias": (
        OrdemDesenvolvimento.objects.order_by()
        .exclude(metodologia_aprovacao__isnull=True)
        .exclude(metodologia_aprovacao__exact="")
        .values_list("metodologia_aprovacao", flat=True)
        .distinct()
),
    }

    return render(request, "ordens_desenvolvimento/lista_ordens.html", context)



@login_required
@permission_required("comercial.add_ordemdesenvolvimento", raise_exception=True)
def cadastrar_ordem_desenvolvimento(request):
    if request.method == "POST":
        form = OrdemDesenvolvimentoForm(request.POST)
        aba = request.POST.get("aba")

        if form.is_valid():
            ordem = form.save(commit=False)

            if aba == "comercial":
                ordem.assinatura_comercial_nome = request.user.get_full_name()
                ordem.assinatura_comercial_email = request.user.email
                ordem.assinatura_comercial_data = timezone.now()

                # Gera hash e registra assinatura (antes do save, como já estava)
                hash_valido = gerar_assinatura(ordem, request.user)
                conteudo_assinado = f"COMERCIAL|{ordem.pk}|{ordem.codigo_brasmol}"
                AssinaturaEletronica.objects.get_or_create(
                    hash=hash_valido,
                    defaults={
                        "conteudo": conteudo_assinado,
                        "usuario": request.user,
                        "origem_model": "OrdemDesenvolvimento",
                        "origem_id": ordem.pk,
                    }
                )

            elif aba == "tecnica":
                ordem.assinatura_tecnica_nome = request.user.get_full_name()
                ordem.assinatura_tecnica_email = request.user.email
                ordem.assinatura_tecnica_data = timezone.now()

                hash_valido = gerar_assinatura(ordem, request.user)
                conteudo_assinado = f"TECNICA|{ordem.pk}|{ordem.codigo_brasmol}"
                AssinaturaEletronica.objects.get_or_create(
                    hash=hash_valido,
                    defaults={
                        "conteudo": conteudo_assinado,
                        "usuario": request.user,
                        "origem_model": "OrdemDesenvolvimento",
                        "origem_id": ordem.pk,
                    }
                )

            # salva para garantir numero/id
            ordem.save()

            # Disparo de alerta In-App (+ modal conforme config)
            try:
                config = AlertaConfigurado.objects.get(
                    tipo="ORDEM_DESENVOLVIMENTO_CRIADA",
                    ativo=True
                )
                exigir_modal = bool(getattr(config, "exigir_confirmacao_modal", False))
                destinatarios = set(config.usuarios.all())
                for g in config.grupos.all():
                    destinatarios.update(g.user_set.all())
            except AlertaConfigurado.DoesNotExist:
                exigir_modal = False
                destinatarios = set()

            url_visualizar = reverse("visualizar_ordem_desenvolvimento", args=[ordem.id])

            if destinatarios:
                for user in destinatarios:
                    # In-app
                    AlertaUsuario.objects.create(
                        usuario=user,
                        titulo=f"🆕 Nova Ordem de Desenvolvimento Nº {ordem.numero}",
                        mensagem=f"Foi cadastrada uma nova OD para o cliente {ordem.cliente}.",
                        tipo="ORDEM_DESENVOLVIMENTO_CRIADA",
                        referencia_id=ordem.id,
                        url_destino=url_visualizar,
                        exige_confirmacao=exigir_modal
                    )

                    # E-mail (opcional: envia se o usuário tiver e-mail)
                    if user.email:
                        send_email_async.delay(
                            subject=f"🆕 Nova Ordem de Desenvolvimento Nº {ordem.numero}",
                            message=f"Uma nova OD foi cadastrada para o cliente {ordem.cliente}.",
                            recipient_list=[user.email],
                        )
            else:
                # Sem destinatários configurados: feedback útil para diagnóstico em DEV
                if settings.DEBUG:
                    messages.warning(
                        request,
                        "Nenhum destinatário configurado em ORDEM_DESENVOLVIMENTO_CRIADA. "
                        "Verifique em ‘Alertas In-App > Gerenciar’."
                    )

            messages.success(request, "Ordem cadastrada com sucesso.")
            return redirect("lista_ordens_desenvolvimento")
    else:
        form = OrdemDesenvolvimentoForm()

    return render(request, "ordens_desenvolvimento/form_ordem_desenvolvimento.html", {
        "form": form,
        "titulo": "Cadastrar Ordem de Desenvolvimento",
        "ordem": None,
    })


@login_required
@permission_required("comercial.change_ordemdesenvolvimento", raise_exception=True)
def editar_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(OrdemDesenvolvimento, pk=pk)
    aba = request.POST.get("aba") if request.method == "POST" else "comercial"

    if request.method == "POST":
        form = OrdemDesenvolvimentoForm(request.POST, instance=ordem)
        if form.is_valid():
            instancia = form.save(commit=False)

            if aba == "comercial":
                instancia.assinatura_comercial_nome = request.user.get_full_name()
                instancia.assinatura_comercial_email = request.user.email
                instancia.assinatura_comercial_data = timezone.now()

                # Mantém assinatura técnica existente
                instancia.assinatura_tecnica_nome = ordem.assinatura_tecnica_nome
                instancia.assinatura_tecnica_email = ordem.assinatura_tecnica_email
                instancia.assinatura_tecnica_data = ordem.assinatura_tecnica_data

                # Gera hash e salva assinatura
                hash_valido = gerar_assinatura(instancia, request.user)
                conteudo_assinado = f"COMERCIAL|{instancia.pk}|{instancia.codigo_brasmol}"

                AssinaturaEletronica.objects.get_or_create(
                    hash=hash_valido,
                    defaults={
                        "conteudo": conteudo_assinado,
                        "usuario": request.user,
                        "origem_model": "OrdemDesenvolvimento",
                        "origem_id": instancia.pk,
                    }
                )

            elif aba == "tecnica":
                instancia.assinatura_tecnica_nome = request.user.get_full_name()
                instancia.assinatura_tecnica_email = request.user.email
                instancia.assinatura_tecnica_data = timezone.now()

                # Mantém assinatura comercial existente
                instancia.assinatura_comercial_nome = ordem.assinatura_comercial_nome
                instancia.assinatura_comercial_email = ordem.assinatura_comercial_email
                instancia.assinatura_comercial_data = ordem.assinatura_comercial_data

                hash_valido = gerar_assinatura(instancia, request.user)
                conteudo_assinado = f"TECNICA|{instancia.pk}|{instancia.codigo_brasmol}"

                AssinaturaEletronica.objects.get_or_create(
                    hash=hash_valido,
                    defaults={
                        "conteudo": conteudo_assinado,
                        "usuario": request.user,
                        "origem_model": "OrdemDesenvolvimento",
                        "origem_id": instancia.pk,
                    }
                )

            # Debug
            print("🟡 DEBUG — prazo_amostra:", form.cleaned_data.get("prazo_amostra"))

            instancia.save()
            messages.success(request, "Ordem atualizada com sucesso.")
            return redirect("lista_ordens_desenvolvimento")

    else:
        form = OrdemDesenvolvimentoForm(instance=ordem)

    return render(request, "ordens_desenvolvimento/form_ordem_desenvolvimento.html", {
        "form": form,
        "titulo": f"Editar Ordem de Desenvolvimento Nº {ordem.numero:03d}",
        "ordem": ordem,
    })


@login_required
@permission_required("comercial.view_ordemdesenvolvimento", raise_exception=True)
def visualizar_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(
        OrdemDesenvolvimento.objects.select_related(
            "precalculo__cotacao",
            "usuario_comercial__funcionario__cargo_atual",
            "usuario_tecnico__funcionario__cargo_atual"
        ),
        pk=pk
    )

    razoes_choices = OrdemDesenvolvimento._meta.get_field("razao").choices
    cotacao_numero = ordem.precalculo.cotacao.numero if ordem.precalculo and ordem.precalculo.cotacao else None
    precalculo_numero = ordem.precalculo.numero if ordem.precalculo else None

    # Geração de dados para assinatura com QR Code
    assinaturas_qr = {}

    for aba in ["comercial", "tecnica"]:
        try:
            assinatura = (
                AssinaturaEletronica.objects
                .filter(origem_model="OrdemDesenvolvimento", origem_id=ordem.pk, conteudo__icontains=aba.upper())
                .latest("data_assinatura")
            )

            assinaturas_qr[aba] = {
                "nome": assinatura.usuario.get_full_name(),
                "departamento": (
                    getattr(getattr(assinatura.usuario, "funcionario", None), "cargo_atual", None).nome
                    if hasattr(assinatura.usuario, "funcionario") else ""
                ),
                "email": assinatura.usuario.email,
                "data": assinatura.data_assinatura,
                "hash": assinatura.hash,
                "qr": gerar_qrcode_base64(
                    request.build_absolute_uri(
                        reverse("validar_assinatura", args=[assinatura.hash])
                    )
                ),
            }
        except AssinaturaEletronica.DoesNotExist:
            assinaturas_qr[aba] = None

    return render(request, "ordens_desenvolvimento/visualizar_f017.html", {
        "ordem": ordem,
        "razoes_choices": razoes_choices,
        "cotacao_numero": cotacao_numero,
        "precalculo_numero": precalculo_numero,
        "assinaturas_qr": assinaturas_qr,
    })




@login_required
@permission_required("comercial.delete_ordemdesenvolvimento", raise_exception=True)
def excluir_ordem_desenvolvimento(request, pk):
    ordem = get_object_or_404(OrdemDesenvolvimento, pk=pk)
    if request.method == "POST":
        ordem.delete()
        return redirect("lista_ordens_desenvolvimento")
    return render(request, "partials/global/_modal_exclusao.html", {
        "objeto": ordem,
        "url_exclusao": "excluir_ordem_desenvolvimento",
        "titulo": "Excluir Ordem de Desenvolvimento"
    })
