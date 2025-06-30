from datetime import date

from Funcionario.models import Treinamento, AvaliacaoTreinamento


def processar_lista_presenca(lista_presenca):
    """Processa os dados da lista de presença para atualizar/gerar treinamentos e avaliações."""
    if lista_presenca.situacao in ["finalizado", "em_andamento"] and lista_presenca.planejado == "sim":
        treinamento_existente = None

        if lista_presenca.treinamento and str(lista_presenca.treinamento).isdigit():
            treinamento_existente = Treinamento.objects.filter(id=int(lista_presenca.treinamento)).first()

        if not treinamento_existente:
            treinamento_existente = Treinamento.objects.filter(
                nome_curso=lista_presenca.assunto
            ).order_by("-data_inicio").first()

        if treinamento_existente:
            treinamento_existente.nome_curso = lista_presenca.assunto
            treinamento_existente.data_inicio = lista_presenca.data_inicio
            treinamento_existente.data_fim = lista_presenca.data_fim
            treinamento_existente.carga_horaria = lista_presenca.duracao
            treinamento_existente.descricao = lista_presenca.descricao
            treinamento_existente.status = (
                "planejado" if lista_presenca.situacao == "em_andamento" else "concluido"
            )
            treinamento_existente.planejado = lista_presenca.planejado
            treinamento_existente.save()
            treinamento_existente.funcionarios.clear()
        else:
            treinamento_existente = Treinamento.objects.create(
                tipo="interno",
                categoria="treinamento",
                nome_curso=lista_presenca.assunto,
                instituicao_ensino="Bras-Mol",
                status="planejado" if lista_presenca.situacao == "em_andamento" else "concluido",
                data_inicio=lista_presenca.data_inicio,
                data_fim=lista_presenca.data_fim,
                carga_horaria=lista_presenca.duracao,
                descricao=lista_presenca.descricao,
                situacao="aprovado",
                planejado=lista_presenca.planejado,
            )
            lista_presenca.treinamento = str(treinamento_existente.id)
            lista_presenca.save()

        for participante in lista_presenca.participantes.all():
            treinamento_existente.funcionarios.add(participante)

        if lista_presenca.necessita_avaliacao:
            for participante in lista_presenca.participantes.all():
                avaliacao, criada = AvaliacaoTreinamento.objects.get_or_create(
                    funcionario=participante,
                    treinamento=treinamento_existente,
                    defaults={
                        "data_avaliacao": lista_presenca.data_fim or date.today(),
                        "periodo_avaliacao": 60,
                        "pergunta_1": None,
                        "pergunta_2": None,
                        "pergunta_3": None,
                        "responsavel_1": participante.responsavel,
                        "descricao_melhorias": "Aguardando avaliação",
                        "avaliacao_geral": None,
                    },
                )
                if not criada:
                    avaliacao.data_avaliacao = lista_presenca.data_fim or date.today()
                    avaliacao.pergunta_1 = None
                    avaliacao.pergunta_2 = None
                    avaliacao.pergunta_3 = None
                    avaliacao.responsavel_1 = participante.responsavel
                    avaliacao.descricao_melhorias = "Aguardando avaliação"
                    avaliacao.avaliacao_geral = None
                    avaliacao.save()
