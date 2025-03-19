import os

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from Funcionario.models import (
    AvaliacaoAnual,
    Cargo,
    Funcionario,
    Revisao,
    Settings,
    Treinamento,
)


def get_funcionario_info(request, id):
    try:
        # Obter o funcionário
        funcionario = Funcionario.objects.get(id=id)

        # Obter dados do cargo atual
        cargo_atual = funcionario.cargo_atual
        descricao_cargo = ""
        if cargo_atual:
            descricao_cargo = f"Descrição de cargo N° {cargo_atual.numero_dc} - Nome: {cargo_atual.nome}"

        # Obter a última revisão do cargo
        ultima_revisao = (
            Revisao.objects.filter(cargo=cargo_atual).order_by("-data_revisao").first()
        )
        numero_revisao = (
            ultima_revisao.numero_revisao
            if ultima_revisao
            else "Nenhuma revisão encontrada"
        )

        # Obter a última avaliação anual do funcionário
        ultima_avaliacao_anual = (
            AvaliacaoAnual.objects.filter(funcionario=funcionario)
            .order_by("-data_avaliacao")
            .first()
        )

        # Processar a data e o status da última avaliação de desempenho
        ultima_avaliacao_data = (
            ultima_avaliacao_anual.data_avaliacao.strftime("%d/%m/%Y")
            if ultima_avaliacao_anual
            else "Data não encontrada"
        )
        ultima_avaliacao_status = (
            ultima_avaliacao_anual.calcular_classificacao()["status"]
            if ultima_avaliacao_anual
            else "Status não encontrado"
        )

        # Formatar as informações para resposta JSON
        data = {
            "nome": funcionario.nome,
            "local_trabalho": funcionario.local_trabalho,
            "cargo_atual": cargo_atual.nome if cargo_atual else "",
            "escolaridade": funcionario.escolaridade,
            "competencias": f"{descricao_cargo}, Última Revisão N° {numero_revisao}",
            "data_ultima_avaliacao": ultima_avaliacao_data,
            "status_ultima_avaliacao": ultima_avaliacao_status,
        }
        return JsonResponse(data)

    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_treinamentos(request, funcionario_id):
    try:
        # Filtra os treinamentos do funcionário e retorna todos os campos relevantes
        treinamentos = (
            Treinamento.objects.filter(funcionarios__id=funcionario_id)
            .values(
                "id",  # ID do treinamento
                "tipo",  # Tipo de treinamento
                "nome_curso",  # Nome do curso
                "categoria",  # Categoria do treinamento
                "status",  # Status do treinamento
                "data_fim",  # Data de conclusão
            )
            .order_by("data_fim")
        )  # Ordenar por data de conclusão

        return JsonResponse(list(treinamentos), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def get_treinamentos_por_funcionario(request, funcionario_id):
    try:
        # Verifique se o funcionário existe
        funcionario = Funcionario.objects.get(id=funcionario_id)

        # Obtenha os treinamentos associados ao funcionário
        treinamentos = Treinamento.objects.filter(funcionarios=funcionario).values(
            "id", "nome_curso", "data_fim"
        )

        # Retorne os treinamentos como JSON
        return JsonResponse(list(treinamentos), safe=False)

    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_competencias(request):
    try:
        competencias = Cargo.objects.all()
        competencias_data = []

        for competencia in competencias:
            # Tente buscar a última revisão; se não houver, registre um valor padrão
            ultima_revisao = competencia.revisoes.order_by("-data_revisao").first()
            competencias_data.append(
                {
                    "id": competencia.id,
                    "numero_dc": competencia.numero_dc,
                    "nome": competencia.nome,
                    "numero_revisao": (
                        ultima_revisao.numero_revisao
                        if ultima_revisao
                        else "Sem revisão"
                    ),
                    "data_revisao": (
                        ultima_revisao.data_revisao.strftime("%d/%m/%Y")
                        if ultima_revisao
                        else "Sem data"
                    ),
                }
            )

        return JsonResponse(competencias_data, safe=False)

    except Exception as e:
        # Log detalhado para análise de erro
        print(f"Erro ao carregar competências: {e}")
        return JsonResponse(
            {"error": f"Erro ao carregar as competências: {e}"}, status=500
        )


def get_cargo(request, funcionario_id):
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
        data = {
            "cargo": (
                funcionario.cargo_atual.nome
                if funcionario.cargo_atual
                else "Cargo não encontrado"
            ),
            "departamento": funcionario.local_trabalho or "Departamento não encontrado",
            "responsavel": (
                {
                    "id": funcionario.responsavel.id,
                    "nome": funcionario.responsavel.nome,
                }
                if funcionario.responsavel
                else "Responsável não encontrado"
            ),
        }
        return JsonResponse(data)
    except Funcionario.DoesNotExist:
        return JsonResponse(
            {
                "cargo": "Não encontrado",
                "departamento": "Não encontrado",
                "responsavel": "Não encontrado",
            },
            status=404,
        )


def get_funcionario_ficha(request, id):
    try:
        funcionario = Funcionario.objects.get(id=id)

        # Coletando informações básicas do funcionário
        data = {
            "nome": funcionario.nome,
            "data_admissao": funcionario.data_admissao,
            "cargo_atual": (
                funcionario.cargo_atual.nome if funcionario.cargo_atual else ""
            ),
            "local_trabalho": funcionario.local_trabalho,
            "escolaridade": funcionario.escolaridade,
            "status": funcionario.status,
            "foto": funcionario.foto.url if funcionario.foto else None,
            "curriculo": funcionario.curriculo.url if funcionario.curriculo else None,
        }

        # Avaliações de Desempenho
        avaliacoes_desempenho = AvaliacaoDesempenho.objects.filter(
            funcionario=funcionario
        ).values(
            "data_avaliacao",
            "centro_custo",
            "gerencia",
            "avaliador__nome",
            "postura_seg_trabalho",
            "qualidade_produtividade",
            "trabalho_em_equipe",
            "comprometimento",
            "disponibilidade_para_mudancas",
            "disciplina",
            "rendimento_sob_pressao",
            "proatividade",
            "comunicacao",
            "assiduidade",
            "observacoes",
        )
        data["avaliacoes_desempenho"] = list(avaliacoes_desempenho)

        # Avaliações de Treinamento
        avaliacoes_treinamento = (
            AvaliacaoTreinamento.objects.filter(funcionario=funcionario)
            .select_related("treinamento")
            .values(
                "data_avaliacao",
                "treinamento__id",  # ID do treinamento
                "treinamento__assunto",  # Acesso ao assunto do treinamento através da relação correta
                "responsavel_1_nome",
                "responsavel_2_nome",
                "responsavel_3_nome",
                "avaliacao_geral",
            )
        )
        data["avaliacoes_treinamento"] = list(avaliacoes_treinamento)

        # Treinamentos
        treinamentos = Treinamento.objects.filter(funcionario=funcionario).values(
            "tipo", "nome_curso", "categoria", "data_inicio", "data_fim", "status"
        )
        data["treinamentos"] = list(treinamentos)

        # Avaliações de Job Rotation
        job_rotations = JobRotationEvaluation.objects.filter(
            funcionario=funcionario
        ).values(
            "area_atual",
            "nova_funcao__nome",
            "data_inicio",
            "termino_previsto",
            "avaliacao_gestor",
            "avaliacao_funcionario",
            "avaliacao_rh",
        )
        data["job_rotations"] = list(job_rotations)

        return JsonResponse(data, safe=False)

    except Funcionario.DoesNotExist:
        return JsonResponse({"error": "Funcionário não encontrado"}, status=404)


@csrf_exempt
def atualizar_cargo_funcionario(request, funcionario_id):
    if request.method == "POST":
        try:
            novo_cargo_id = request.POST.get("novo_cargo")
            funcionario = Funcionario.objects.get(id=funcionario_id)
            novo_cargo = Cargo.objects.get(id=novo_cargo_id)

            funcionario.cargo_atual = novo_cargo
            funcionario.save()

            return JsonResponse({"status": "success"}, status=200)
        except Funcionario.DoesNotExist:
            return JsonResponse({"error": "Funcionário não encontrado"}, status=404)
        except Cargo.DoesNotExist:
            return JsonResponse({"error": "Cargo não encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Método não permitido"}, status=405)


def funcionario_api(request, funcionario_id):
    # Obtemos o funcionário pelo ID
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    settings = Settings.objects.first()

    # Verificamos se `responsavel` é um objeto e obtemos o cargo associado
    responsavel_nome = (
        funcionario.responsavel.nome
        if hasattr(funcionario.responsavel, "nome")
        else funcionario.responsavel
    )
    cargo_responsavel = (
        funcionario.responsavel.cargo.nome
        if hasattr(funcionario.responsavel, "cargo")
        else "N/A"
    )

    # Montamos os dados a serem retornados
    data = {
        "nome": funcionario.nome,
        "cargo_atual": (
            funcionario.cargo_atual.nome
            if hasattr(funcionario.cargo_atual, "nome")
            else funcionario.cargo_atual
        ),
        "responsavel": responsavel_nome,
        "cargo_responsavel": cargo_responsavel,
        "settings": {
            "nome_empresa": settings.nome_empresa,
        },
        "data_atual": now().strftime("%d de %B de %Y"),
    }
    return JsonResponse(data)
