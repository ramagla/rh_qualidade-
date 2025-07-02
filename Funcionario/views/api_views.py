# Third-party
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

# Local
from Funcionario.models import (
    AvaliacaoAnual,
    Cargo,
    Funcionario,
    Settings,
    Treinamento,
    AvaliacaoTreinamento,
    JobRotationEvaluation,
)
from Funcionario.utils.utils_funcionario import (
    montar_info_funcionario,
    buscar_treinamentos_funcionario
)


def get_funcionario_info(request, id):
    """Retorna informações detalhadas de um funcionário."""
    try:
        funcionario = get_object_or_404(Funcionario, id=id)
        data = montar_info_funcionario(funcionario)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_treinamentos(request, funcionario_id):
    """Retorna os treinamentos associados a um funcionário específico."""
    try:
        treinamentos = buscar_treinamentos_funcionario(funcionario_id)
        return JsonResponse(list(treinamentos), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def get_treinamentos_por_funcionario(request, funcionario_id):
    """Retorna treinamentos por funcionário."""
    try:
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        treinamentos = Treinamento.objects.filter(funcionarios=funcionario).values(
            "id", "nome_curso", "data_fim"
        )
        return JsonResponse(list(treinamentos), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_competencias(request):
    """Retorna as competências dos cargos e suas últimas revisões."""
    try:
        competencias_data = []
        for competencia in Cargo.objects.all():
            ultima_revisao = competencia.revisoes.order_by("-data_revisao").first()
            competencias_data.append({
                "id": competencia.id,
                "numero_dc": competencia.numero_dc,
                "nome": competencia.nome,
                "numero_revisao": ultima_revisao.numero_revisao if ultima_revisao else "Sem revisão",
                "data_revisao": ultima_revisao.data_revisao.strftime("%d/%m/%Y") if ultima_revisao else "Sem data",
            })
        return JsonResponse(competencias_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": f"Erro ao carregar as competências: {e}"}, status=500)


def get_cargo(request, funcionario_id):
    """Retorna informações do cargo e responsável do funcionário."""
    try:
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        data = {
            "cargo": funcionario.cargo_atual.nome if funcionario.cargo_atual else "Cargo não encontrado",
            "departamento": str(funcionario.local_trabalho) if funcionario.local_trabalho else "Departamento não encontrado",
            "responsavel": {
                "id": funcionario.responsavel.id,
                "nome": funcionario.responsavel.nome,
            } if funcionario.responsavel else "Responsável não encontrado",
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse({
            "cargo": "Não encontrado",
            "departamento": "Não encontrado",
            "responsavel": "Não encontrado",
        }, status=404)


def get_funcionario_ficha(request, id):
    """Retorna ficha completa do funcionário, incluindo avaliações e treinamentos."""
    try:
        funcionario = get_object_or_404(Funcionario, id=id)
        data = {
            "nome": funcionario.nome,
            "data_admissao": funcionario.data_admissao,
            "cargo_atual": funcionario.cargo_atual.nome if funcionario.cargo_atual else "",
            "local_trabalho": funcionario.local_trabalho,
            "escolaridade": funcionario.escolaridade,
            "status": funcionario.status,
            "foto": funcionario.foto.url if funcionario.foto else None,
            "curriculo": funcionario.curriculo.url if funcionario.curriculo else None,
        }
        avaliacoes_desempenho = AvaliacaoAnual.objects.filter(funcionario=funcionario).values(
            "data_avaliacao", "centro_custo", "funcionario__cargo_atual__departamento",
            "postura_seg_trabalho", "qualidade_produtividade", "trabalho_em_equipe",
            "comprometimento", "disponibilidade_para_mudancas", "disciplina",
            "rendimento_sob_pressao", "proatividade", "comunicacao", "assiduidade",
            "avaliacao_global_avaliador", "avaliacao_global_avaliado",
        )
        data["avaliacoes_desempenho"] = list(avaliacoes_desempenho)

        avaliacoes_treinamento = AvaliacaoTreinamento.objects.filter(funcionario=funcionario).select_related("treinamento").values(
            "data_avaliacao", "treinamento__id", "treinamento__nome_curso",
            "responsavel_1__nome", "responsavel_2__nome", "responsavel_3__nome", "avaliacao_geral"
        )
        data["avaliacoes_treinamento"] = list(avaliacoes_treinamento)

        treinamentos = Treinamento.objects.filter(funcionarios=funcionario).values(
            "tipo", "nome_curso", "categoria", "data_inicio", "data_fim", "status"
        )
        data["treinamentos"] = list(treinamentos)

        job_rotations = JobRotationEvaluation.objects.filter(funcionario=funcionario).values(
            "area", "nova_funcao__nome", "data_inicio", "termino_previsto",
            "avaliacao_gestor", "avaliacao_funcionario", "avaliacao_rh",
        )
        data["job_rotations"] = list(job_rotations)

        return JsonResponse(data, safe=False)
    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)


@csrf_exempt
def atualizar_cargo_funcionario(request, funcionario_id):
    """Atualiza o cargo atual de um funcionário via POST."""
    if request.method == "POST":
        try:
            novo_cargo_id = request.POST.get("novo_cargo")
            funcionario = get_object_or_404(Funcionario, id=funcionario_id)
            novo_cargo = get_object_or_404(Cargo, id=novo_cargo_id)
            funcionario.cargo_atual = novo_cargo
            funcionario.save()
            return JsonResponse({"status": "success"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Método não permitido"}, status=405)


def funcionario_api(request, funcionario_id):
    """Retorna dados do funcionário para exibição na interface."""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()
    responsavel_nome = getattr(funcionario.responsavel, "nome", funcionario.responsavel)
    cargo_responsavel = getattr(funcionario.responsavel.cargo, "nome", "N/A")
    data = {
        "nome": funcionario.nome,
        "cargo_atual": getattr(funcionario.cargo_atual, "nome", funcionario.cargo_atual),
        "responsavel": responsavel_nome,
        "cargo_responsavel": cargo_responsavel,
        "settings": {
            "nome_empresa": settings.nome_empresa,
        },
        "data_atual": now().strftime("%d de %B de %Y"),
    }
    return JsonResponse(data)
