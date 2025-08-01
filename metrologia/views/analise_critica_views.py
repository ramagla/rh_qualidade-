from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import now

from alerts import models as alert_models
from assinatura_eletronica.models import AssinaturaEletronica
from assinatura_eletronica.utils import gerar_assinatura, gerar_qrcode_base64
from metrologia.forms.AnaliseCriticaForm import AnaliseCriticaMetrologiaForm
from metrologia.models import AnaliseCriticaMetrologia


@login_required
@permission_required('metrologia.view_análisecríticametrologia', raise_exception=True)
def lista_analise_critica(request):
    qs = AnaliseCriticaMetrologia.objects.all().order_by('-assinado_em')

    # filtro por código de equipamento
    codigo = request.GET.get('equipamento')
    if codigo:
        qs = qs.filter(
            Q(equipamento_instrumento__codigo__icontains=codigo) |
            Q(equipamento_dispositivo__codigo__icontains=codigo)
        )

    total_analises = qs.count()
    total_nc_critica = qs.filter(compromete_qualidade=True).count()
    total_cliente_notificado = qs.filter(comunicar_cliente=True).count()

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'analise_critica/lista_analise_critica.html', {
        'page_obj': page_obj,
        'total_analises': total_analises,
        'total_nc_critica': total_nc_critica,
        'total_cliente_notificado': total_cliente_notificado,
    })


from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now


from datetime import datetime


@login_required
@permission_required("metrologia.add_análisecríticametrologia", raise_exception=True)
def cadastrar_analise_critica(request):
    form = AnaliseCriticaMetrologiaForm(request.POST or None)
    if form.is_valid():
        # 1) salva a análise
        analise = form.save(commit=False)
        analise.usuario = request.user
        analise.data_assinatura = now()
        analise.assinatura_nome = request.user.get_full_name()
        analise.assinatura_cn = request.user.email


        analise.descricao_equipamento = request.POST.get("descricao_equipamento") or ""
        analise.modelo = request.POST.get("modelo") or ""
        analise.capacidade_medicao = request.POST.get("capacidade_medicao") or ""

        data_br = request.POST.get("data_ultima_calibracao")
        if data_br:
            try:
                analise.data_ultima_calibracao = datetime.strptime(data_br, "%Y-%m-%d").date()
            except ValueError:
                analise.data_ultima_calibracao = None
        analise.save()  # salva antes de gerar o hash

        # 2) gera hash e conteúdo padronizado
        hash_val = gerar_assinatura(analise, request.user)
        conteudo_assinado = (
            f"METROLOGIA|{analise.pk}|"
            f"{analise.equipamento_dispositivo or analise.equipamento_instrumento}"
        )

        # 3) cria ou atualiza a assinatura eletrônica
        assin_obj, created = AssinaturaEletronica.objects.update_or_create(
            origem_model="AnaliseCriticaMetrologia",
            origem_id=analise.pk,
            defaults={
                "hash": hash_val,
                "conteudo": conteudo_assinado,
                "usuario": request.user,
                "data_assinatura": analise.data_assinatura,
            }
        )

        # DEBUG: confirma no console
        print(
            "🟢 [AssinaturaEletronica] "
            f"{'Criada' if created else 'Atualizada'} – "
            f"ID={assin_obj.id}, Hash={assin_obj.hash}, "
            f"Origem={assin_obj.origem_model}#{assin_obj.origem_id}"
        )

        return redirect("lista_analise_critica")

    return render(request, "analise_critica/form_analise_critica.html", {
        "form": form,
        "titulo": "Cadastrar Análise Crítica",
        "icone": "bi bi-plus-circle",
        "acao": "Cadastrar"
    })


@login_required
@permission_required("metrologia.change_análisecríticametrologia", raise_exception=True)
def editar_analise_critica(request, id):
    analise = get_object_or_404(AnaliseCriticaMetrologia, id=id)
    form = AnaliseCriticaMetrologiaForm(request.POST or None, instance=analise)

    if form.is_valid():
        # 1) salva a análise (o form já atribui corretamente o campo 'tipo')
        analise = form.save(commit=False)
        analise.descricao_equipamento = request.POST.get("descricao_equipamento") or ""
        analise.modelo = request.POST.get("modelo") or ""
        analise.capacidade_medicao = request.POST.get("capacidade_medicao") or ""

        data_br = request.POST.get("data_ultima_calibracao")
        print("📆 Valor recebido no POST para data_ultima_calibracao:", data_br)

        if data_br:
            try:
                analise.data_ultima_calibracao = data_br or None
                print("✅ Data convertida com sucesso:", analise.data_ultima_calibracao)

            except ValueError:
                print("❌ Erro ao converter a data:", data_br)
                analise.data_ultima_calibracao = None

        analise.save()

        # 2) gera hash e conteúdo padronizado
        hash_val = gerar_assinatura(analise, request.user)
        conteudo_assinado = (
            f"METROLOGIA|{analise.pk}|"
            f"{analise.equipamento_dispositivo or analise.equipamento_instrumento}"
        )

        # 3) cria ou atualiza a assinatura eletrônica
        assin_obj, created = AssinaturaEletronica.objects.update_or_create(
            origem_model="AnaliseCriticaMetrologia",
            origem_id=analise.pk,
            defaults={
                "hash": hash_val,
                "conteudo": conteudo_assinado,
                "usuario": request.user,
                "data_assinatura": analise.data_assinatura or now(),
            }
        )

        # DEBUG: confirma no console
        print(
            "🟢 [AssinaturaEletronica] "
            f"{'Criada' if created else 'Atualizada'} – "
            f"ID={assin_obj.id}, Hash={assin_obj.hash}, "
            f"Origem={assin_obj.origem_model}#{assin_obj.origem_id}"
        )

        return redirect("lista_analise_critica")

    return render(request, "analise_critica/form_analise_critica.html", {
        "form": form,
        "titulo": "Editar Análise Crítica",
        "icone": "bi bi-pencil-square",
        "acao": "Salvar Alterações"
    })



@login_required
@permission_required("metrologia.view_análisecríticametrologia", raise_exception=True)
def visualizar_analise_critica(request, id):
    analise = get_object_or_404(AnaliseCriticaMetrologia, id=id)

    try:
        # já traz a FK usuario→funcionario→cargo_atual para evitar queries extras
        assinatura = (
            AssinaturaEletronica.objects
            .filter(origem_model="AnaliseCriticaMetrologia", origem_id=analise.pk)
            .select_related("usuario__funcionario__cargo_atual")
            .latest("data_assinatura")
        )

        # monta o dict com todas as chaves que o partial espera
        assinatura_qr = {
            "nome": assinatura.usuario.get_full_name(),
            # aqui usamos o cargo_atual.nome como 'departamento' (o partial rotula como Cargo)
            "departamento": (
                assinatura.usuario.funcionario.cargo_atual.nome
                if hasattr(assinatura.usuario, "funcionario")
                   and assinatura.usuario.funcionario.cargo_atual
                else ""
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
        assinatura_qr = None

    return render(request, "analise_critica/visualizar_analise_critica.html", {
        "analise":       analise,
        "titulo":        "Visualizar Análise Crítica",
        "icone":         "bi bi-eye-fill",
        "assinatura_qr": assinatura_qr,
    })

@login_required
@permission_required("metrologia.delete_análisecríticametrologia", raise_exception=True)
def excluir_analise_critica(request, id):
    analise = get_object_or_404(AnaliseCriticaMetrologia, id=id)
    if request.method == "POST":
        analise.delete()
        return redirect("lista_analise_critica")
    return render(request, "partials/global/_confirmar_exclusao.html", {
        "objeto": analise,
        "url_voltar": "lista_analise_critica",
        "entidade": "análise crítica"
    })
