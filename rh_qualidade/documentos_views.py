from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from Funcionario.forms import DocumentoForm, RevisaoDocForm
from Funcionario.models.documentos import Documento, RevisaoDoc


from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from qualidade_fornecimento.models.f045 import User

@login_required
def lista_documentos(request):
    nome = request.GET.get("nome", "")
    status = request.GET.get("status", "")
    codigo = request.GET.get("codigo", "")
    departamento = request.GET.get("departamento", "")

    documentos = Documento.objects.all()

    # 🔐 Filtrar pelos departamentos do funcionário logado
    if request.user.is_authenticated and hasattr(request.user, "funcionario"):
        usuarios_liberados = ["rafael.almeida", "Agoveia", "Dpereira"]

        if request.user.username not in usuarios_liberados:
            departamento_usuario = request.user.funcionario.local_trabalho
            if departamento_usuario:
                documentos = documentos.filter(departamentos=departamento_usuario)

    # Aplicar filtros adicionais (nome, status, codigo, departamento)
    if nome:
        documentos = documentos.filter(nome__icontains=nome)
    if status:
        documentos = documentos.filter(status=status)
    if codigo:
        documentos = documentos.filter(codigo__icontains=codigo)
    if departamento:
        documentos = documentos.filter(departamentos__id=departamento)

    # Filtros disponíveis no template
    documentos_distinct = documentos.values("nome").distinct()
    codigos_distinct = documentos.values("codigo").distinct()
    departamentos_distinct = documentos.values_list("departamentos__id", "departamentos__nome").distinct()
    status_choices = Documento.STATUS_CHOICES


    # Indicadores
    total_documentos = documentos.count()
    total_aprovados = documentos.filter(status="aprovado").count()
    total_em_revisao = documentos.filter(status="em_revisao").count()
    total_inativos = documentos.filter(status="inativo").count()

    # Paginação
    paginator = Paginator(documentos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "documentos": page_obj,
        "documentos_distinct": documentos_distinct,
        "codigos_distinct": codigos_distinct,
        "departamentos_distinct": departamentos_distinct,
        "status_choices": status_choices,
        "total_documentos": total_documentos,
        "total_aprovados": total_aprovados,
        "total_em_revisao": total_em_revisao,
        "total_inativos": total_inativos,
    }


    return render(request, "documentos/lista_documentos.html", context)


def _salvar_documento(request, documento_id=None):
    if documento_id:
        documento = get_object_or_404(Documento, id=documento_id)
        edicao = True
    else:
        documento = None
        edicao = False

    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            form.save()
            msg = "Documento atualizado com sucesso!" if edicao else "Documento cadastrado com sucesso!"
            messages.success(request, msg)
            return redirect("lista_documentos")
    else:
        form = DocumentoForm(instance=documento)

    context = {
        "form": form,
        "edicao": edicao,
        "documento": documento,
        "url_voltar": "lista_documentos",
        "param_id": None,  # ou simplesmente omitir completamente essa linha
    }

    return render(request, "documentos/form_documento.html", context)



@login_required
def cadastrar_documento(request):
    return _salvar_documento(request)


@login_required
def editar_documento(request, documento_id):
    return _salvar_documento(request, documento_id=documento_id)


@login_required
def excluir_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    documento.delete()
    messages.success(request, "Documento excluído com sucesso!")
    return redirect("lista_documentos")


@login_required
def historico_documentos(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    revisoes = RevisaoDoc.objects.filter(documento=documento, status="ativo")

    # Para cada revisão, gera quem leu e quem falta
    colaboradores_por_departamento = User.objects.filter(
        funcionario__local_trabalho__in=documento.departamentos.all(),
        funcionario__status="Ativo"
    ).distinct()


    revisao_leituras = {}
    revisao_faltantes = {}

    for revisao in revisoes:
        leitores_ids = RevisaoDocLeitura.objects.filter(revisao=revisao).values_list("usuario_id", flat=True)
        leitores = User.objects.filter(id__in=leitores_ids)
        faltantes = colaboradores_por_departamento.exclude(id__in=leitores_ids)

        revisao_leituras[revisao.id] = leitores
        revisao_faltantes[revisao.id] = faltantes

    return render(
        request,
        "documentos/historico_revisoes.html",
        {
            "documento": documento,
            "revisoes": revisoes,
            "revisao_leituras": revisao_leituras,
            "revisao_faltantes": revisao_faltantes,
        },
    )



@login_required
def adicionar_documento(request, documento_id):
    documento = get_object_or_404(Documento, id=documento_id)
    if request.method == "POST":
        form = RevisaoDocForm(request.POST)
        if form.is_valid():
            revisao = form.save(commit=False)
            revisao.documento = documento
            revisao.save()
            messages.success(request, "Revisão adicionada com sucesso.")
            return redirect("historico_documentos", documento_id=documento.id)
    else:
        form = RevisaoDocForm()
    return render(
        request,
        "documentos/adicionar_revisao.html",
        {"form": form, "documento": documento},
    )


@login_required
def excluir_revisao2(request, revisao_id):
    revisao = get_object_or_404(RevisaoDoc, id=revisao_id)
    documento_id = revisao.documento.id  # Salva o ID do documento antes da exclusão
    revisao.delete()  # Exclui a revisão do banco de dados
    messages.success(request, "Revisão excluída com sucesso.")
    return redirect("historico_documentos", documento_id=documento_id)


from Funcionario.models.revisao_doc_leitura import RevisaoDocLeitura
from Funcionario.models.documentos import RevisaoDoc
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
def get_ultima_revisao_nao_lida(request):
    if request.user.is_authenticated and hasattr(request.user, "funcionario"):
        departamento_usuario = request.user.funcionario.local_trabalho

        if departamento_usuario:
            # Busca TODAS revisões ativas de documentos do departamento do usuário
            revisoes = RevisaoDoc.objects.filter(
                status="ativo",
                documento__departamentos=departamento_usuario
            ).order_by("-data_revisao")

            # Agora percorre para achar a primeira que o usuário NÃO leu
            for revisao in revisoes:
                lida = RevisaoDocLeitura.objects.filter(usuario=request.user, revisao=revisao).exists()

                if not lida:
                    # encontrou revisão não lida → mostra popup
                   return JsonResponse({
                        "show": True,
                        "id": revisao.id,
                        "descricao": revisao.descricao_mudanca,
                        "pdf_url": revisao.documento.arquivo.url if revisao.documento.arquivo else "",
                        "codigo": revisao.documento.codigo,
                        "nome": revisao.documento.nome,
                        "numero_revisao": revisao.numero_revisao,
                        "data_revisao": revisao.data_revisao.strftime("%d/%m/%Y"),
                    })

    # Se não achou nenhuma pendente → não mostra popup
    return JsonResponse({"show": False})


@require_POST
@login_required
def marcar_revisao_lida(request):
    data = json.loads(request.body)
    revisao_id = data.get("revisao_id")

    try:
        revisao = RevisaoDoc.objects.get(pk=revisao_id)
        RevisaoDocLeitura.objects.get_or_create(usuario=request.user, revisao=revisao)
        return JsonResponse({"status": "ok"})
    except RevisaoDoc.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Revisão não encontrada"}, status=404)