# utils/matriz_utils.py

from django.utils import timezone
from Funcionario.models.matriz_polivalencia import Atividade, Nota


def obter_atividades_com_fixas(departamento_id):
    """
    Retorna todas as atividades do departamento com as atividades fixas adicionadas no final.
    """
    atividades_base = list(Atividade.objects.filter(departamentos=departamento_id))

    atividades_fixas_nomes = [
        "Manter o setor limpo e organizado",
        "Manusear e descartar materiais, resíduos e sucatas",
    ]
    atividades_fixas = list(
        Atividade.objects.filter(nome__in=atividades_fixas_nomes).order_by("nome")
    )

    atividades = atividades_base + [a for a in atividades_fixas if a not in atividades_base]
    return atividades


def gerar_nota_descricao(nota):
    """
    Retorna a descrição textual de cada nível da nota.
    """
    return {
        0: "Não Treinado",
        1: "Tarefas básicas com acompanhamento",
        2: "Tarefas chave com acompanhamento",
        3: "Qualificado sem acompanhamento",
        4: "Qualificador",
    }.get(nota, "")


def salvar_notas_funcionarios(request, form, atividades, funcionarios, is_edit=False, excluir_ids=None):
    """
    Salva a matriz e as notas dos funcionários para as atividades informadas.
    Ignora funcionários na lista `excluir_ids` se fornecida.
    """
    excluir_ids = excluir_ids or []

    if form.is_valid():
        matriz = form.save(commit=False)
        if is_edit:
            matriz.departamento = form.cleaned_data.get("departamento") or matriz.departamento
        matriz.save()

        for funcionario in funcionarios:
            if funcionario.id in excluir_ids:
                continue

            for atividade in atividades:
                nota_key = f"nota_{funcionario.id}_{atividade.id}"
                nota_value = request.POST.get(nota_key)

                if not nota_value or not nota_value.isdigit():
                    continue

                dados_nota = {
                    "pontuacao": int(nota_value),
                    "perfil": request.POST.get(f"perfil_{funcionario.id}", "")
                }

                Nota.objects.update_or_create(
                    matriz=matriz,
                    funcionario=funcionario,
                    atividade=atividade,
                    defaults=dados_nota
                )
        return matriz, True
    return None, False


def processar_colaboradores_para_salvar(request):
    """
    Retorna dois conjuntos:
    - IDs dos colaboradores mantidos (formulário)
    - IDs dos colaboradores removidos
    """
    colaboradores_removidos = request.POST.get("colaboradores_removidos", "")
    ids_removidos = [int(i) for i in colaboradores_removidos.split(",") if i.strip().isdigit()]

    ids_enviados = set()
    for key in request.POST.keys():
        if key.startswith("nota_") or key.startswith("perfil_"):
            parts = key.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                ids_enviados.add(int(parts[1]))

    ids_mantidos = [fid for fid in ids_enviados if fid not in ids_removidos]
    return ids_mantidos, ids_removidos