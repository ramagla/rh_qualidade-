from Funcionario.models import AvaliacaoAnual, Revisao, Treinamento


def montar_info_funcionario(funcionario):
    """Monta os dados detalhados de um funcionário para resposta JSON."""
    cargo_atual = funcionario.cargo_atual
    descricao_cargo = (
        f"Descrição de cargo N° {cargo_atual.numero_dc} - Nome: {cargo_atual.nome}"
        if cargo_atual else ""
    )

    ultima_revisao = Revisao.objects.filter(cargo=cargo_atual).order_by("-data_revisao").first()
    numero_revisao = ultima_revisao.numero_revisao if ultima_revisao else "Nenhuma revisão encontrada"

    ultima_avaliacao = AvaliacaoAnual.objects.filter(funcionario=funcionario).order_by("-data_avaliacao").first()
    ultima_avaliacao_data = (
        ultima_avaliacao.data_avaliacao.strftime("%d/%m/%Y") if ultima_avaliacao else "Data não encontrada"
    )
    ultima_avaliacao_status = (
        ultima_avaliacao.calcular_classificacao()["status"] if ultima_avaliacao else "Status não encontrado"
    )

    return {
        "nome": funcionario.nome,
        "local_trabalho": str(funcionario.local_trabalho) if funcionario.local_trabalho else "",
        "cargo_atual": cargo_atual.nome if cargo_atual else "",
        "escolaridade": funcionario.escolaridade,
        "competencias": f"{descricao_cargo}, Última Revisão N° {numero_revisao}",
        "data_ultima_avaliacao": ultima_avaliacao_data,
        "status_ultima_avaliacao": ultima_avaliacao_status,
    }


def buscar_treinamentos_funcionario(funcionario_id):
    """Retorna os treinamentos vinculados ao funcionário, com data formatada."""
    treinamentos = Treinamento.objects.filter(funcionarios__id=funcionario_id).order_by("data_fim")
    resultado = []

    for t in treinamentos:
        resultado.append({
            "id": t.id,
            "tipo": t.tipo,
            "nome_curso": t.nome_curso,
            "categoria": t.categoria,
            "status": t.status,
            "data_fim": t.data_fim.strftime("%d/%m/%Y") if t.data_fim else "",
        })

    return resultado
