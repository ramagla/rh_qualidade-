# views/matriz_views.py

# Padrão
from typing import List

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# Terceiros
import pandas as pd

# App Interno
from Funcionario.forms.matriz_polivalencia_forms import MatrizPolivalenciaForm
from Funcionario.models.departamentos import Departamentos
from Funcionario.models.funcionario import Funcionario
from Funcionario.models.matriz_polivalencia import  MatrizPolivalencia, Nota
from Funcionario.utils.matriz_utils import (
    obter_atividades_com_fixas,
    gerar_nota_descricao,
    salvar_notas_funcionarios,
    processar_colaboradores_para_salvar
)


@login_required
def lista_matriz_polivalencia(request):
    """Exibe a listagem das matrizes com filtros e indicadores."""
    departamento = request.GET.get("departamento")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    qs = MatrizPolivalencia.objects.all()
    if departamento:
        qs = qs.filter(departamento_id=departamento)
    if data_inicio:
        qs = qs.filter(atualizado_em__gte=data_inicio)
    if data_fim:
        qs = qs.filter(atualizado_em__lte=data_fim)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    total_matrizes = qs.count()
    mes_atual = timezone.now().month
    matrizes_mes = qs.filter(atualizado_em__month=mes_atual).count()
    total_departamentos = Departamentos.objects.filter(matrizes_polivalencia__isnull=False).distinct().count()

    atividades_counts = [m.atividades.count() for m in qs]
    media_atividades = int(sum(atividades_counts) / total_matrizes) if total_matrizes else 0
    mes_ano = timezone.now().strftime('%m/%Y')
    subtitulo_matriz = f"Atualizadas em {mes_ano}"

    return render(request, "matriz_polivalencia/matriz_polivalencia_lista.html", {
        "matrizes": page_obj,
        "departamentos": Departamentos.objects.filter(ativo=True).order_by("nome"),
        "total_matrizes": total_matrizes,
        "matrizes_mes": matrizes_mes,
        "total_departamentos": total_departamentos,
        "media_atividades": media_atividades,
        "mes_ano": mes_ano,
        "subtitulo_matriz": subtitulo_matriz,

    })


@login_required
def cadastrar_matriz_polivalencia(request):
    """Cadastra uma nova matriz de polivalência."""
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    atividades = []

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST)
        departamento = request.POST.get("departamento")
        atividades = obter_atividades_com_fixas(departamento)
        matriz, sucesso = salvar_notas_funcionarios(request, form, atividades, funcionarios)
        if sucesso:
            messages.success(request, "Matriz cadastrada com sucesso.")
            return redirect("cadastrar_matriz_polivalencia" if "salvar_adicionar_nova" in request.POST else "lista_matriz_polivalencia")
        messages.error(request, "Erro ao cadastrar matriz.")
    else:
        form = MatrizPolivalenciaForm()

    return render(request, "matriz_polivalencia/form_matriz.html", {
        "form": form,
        "atividades": atividades,
        "funcionarios_tabela": list(funcionarios.values("id", "nome")),
        "funcionarios_disponiveis": list(funcionarios.values("id", "nome")),
        "departamentos": Departamentos.objects.all(),
        "campos_responsaveis": ["elaboracao", "coordenacao", "validacao"],
        "url_voltar": "lista_matriz_polivalencia",
    })


@login_required
def editar_matriz_polivalencia(request, id):
    """Edita uma matriz existente."""
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    atividades = obter_atividades_com_fixas(matriz.departamento.id)

    funcionarios_com_nota = Funcionario.objects.filter(
        notas__matriz=matriz,
        notas__atividade__in=atividades
    ).distinct().order_by("nome")

    notas_por_funcionario = {
        f.id: {a.id: {"pontuacao": None, "perfil": ""} for a in atividades}
        for f in funcionarios_com_nota
    }

    for nota in Nota.objects.filter(matriz=matriz):
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": nota.pontuacao,
            "perfil": nota.perfil,
        }

    if request.method == "POST":
        form = MatrizPolivalenciaForm(request.POST, instance=matriz)
        ids_mantidos, ids_removidos = processar_colaboradores_para_salvar(request)
        funcionarios_restantes = Funcionario.objects.filter(id__in=ids_mantidos)
        nova_matriz, sucesso = salvar_notas_funcionarios(request, form, atividades, funcionarios_restantes, is_edit=True, excluir_ids=ids_removidos)
        if sucesso:
            Nota.objects.filter(funcionario_id__in=ids_removidos, atividade__in=atividades).delete()
            messages.success(request, "Matriz atualizada com sucesso.")
            return redirect("lista_matriz_polivalencia")
        messages.error(request, "Erro ao atualizar matriz.")
    else:
        form = MatrizPolivalenciaForm(instance=matriz)

    notas_lista = [
        {"funcionario_id": f, "atividade_id": a, **dados}
        for f, atividades_dict in notas_por_funcionario.items()
        for a, dados in atividades_dict.items()
    ]

    return render(request, "matriz_polivalencia/form_matriz.html", {
        "form": form,
        "matriz": matriz,
        "atividades": atividades,
        "funcionarios_tabela": list(funcionarios_com_nota.values("id", "nome")),
        "funcionarios_disponiveis": list(Funcionario.objects.filter(status="Ativo").values("id", "nome")),
        "departamentos": Departamentos.objects.all(),
        "notas_lista": notas_lista,
        "departamento_selecionado": matriz.departamento,
        "campos_responsaveis": ["elaboracao", "coordenacao", "validacao"],
    })


@login_required
def excluir_matriz_polivalencia(request, id):
    """Exclui uma matriz."""
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    if request.method == "POST":
        matriz.delete()
        messages.success(request, "Matriz excluída com sucesso.")
        return redirect("lista_matriz_polivalencia")
    return render(request, "matriz_polivalencia/excluir.html", {"matriz": matriz})


@login_required
def imprimir_matriz(request, id):
    """Renderiza a matriz em modo de impressão com notas por colaborador."""
    matriz = get_object_or_404(MatrizPolivalencia, id=id)
    atividades = obter_atividades_com_fixas(matriz.departamento.id)

    colaboradores = Funcionario.objects.filter(
        notas__matriz=matriz,
        notas__atividade__in=atividades
    ).distinct().order_by("nome")

    notas = Nota.objects.filter(matriz=matriz, funcionario__in=colaboradores, atividade__in=atividades)

    def gerar_grafico_icone(nota):
        return f"icons/barra_{nota if nota in range(5) else 0}.png"

    notas_por_funcionario = {
        f.id: {
            a.id: {
                "pontuacao": None,
                "perfil": "",
                "grafico": "",
                "descricao": "",
                "nivel": "",
            } for a in atividades
        } for f in colaboradores
    }

    for nota in notas:
        p = nota.pontuacao
        notas_por_funcionario[nota.funcionario.id][nota.atividade.id] = {
            "pontuacao": p,
            "perfil": nota.perfil,
            "grafico": gerar_grafico_icone(p),
            "descricao": gerar_nota_descricao(p),
            "nivel": p,
        }

    notas_lista = [
        {"colaborador_id": cid, "atividade_id": aid, **info}
        for cid, atividades_dict in notas_por_funcionario.items()
        for aid, info in atividades_dict.items()
        if info["pontuacao"] is not None
    ]

    colaboradores_com_perfil = [
        {"id": f.id, "nome": f.nome, "perfil": next((n["perfil"] for n in notas_por_funcionario[f.id].values() if n["perfil"]), "")}
        for f in colaboradores
    ]

    return render(request, "matriz_polivalencia/imprimir_matriz.html", {
        "matriz": matriz,
        "atividades": atividades,
        "colaboradores": colaboradores_com_perfil,
        "notas_lista": notas_lista,
        "atividades_fixas_nomes": [
            "manter o setor limpo e organizado",
            "manusear e descartar materiais, resíduos e sucatas",
        ],
    })
