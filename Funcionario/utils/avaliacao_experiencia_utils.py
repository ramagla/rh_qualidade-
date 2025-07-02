def calcular_orientacao(post_data):
    """
    Calcula a orientação e status de uma avaliação com base nos pontos atribuídos.
    """
    try:
        adaptacao = int(post_data.get("adaptacao_trabalho", 0))
        interesse = int(post_data.get("interesse", 0))
        relacionamento = int(post_data.get("relacionamento_social", 0))
        aprendizagem = int(post_data.get("capacidade_aprendizagem", 0))

        total = adaptacao + interesse + relacionamento + aprendizagem
        porcentagem = (total / 16) * 100

        if porcentagem >= 85:
            return "Efetivar", "Ótimo - Efetivar"
        elif porcentagem >= 66:
            return "Efetivar", "Bom - Efetivar"
        elif porcentagem >= 46:
            return "Encaminhar p/ Treinamento", "Regular - Treinamento"
        return "Desligar", "Ruim - Desligar"

    except ValueError:
        return "Indeterminado", "Erro no cálculo"
