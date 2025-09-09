from collections import defaultdict
from copy import deepcopy
from datetime import timedelta
from django.utils import timezone  # ✅ use o timezone do Django
from django.db.models import Q, Count
from Funcionario.models import (
    Funcionario,
    Departamentos,
    AvaliacaoAnual,
    AvaliacaoExperiencia,
    Treinamento,
    AvaliacaoTreinamento,
    JobRotationEvaluation,
    ListaPresenca,
    IntegracaoFuncionario,
)
from metrologia.models import TabelaTecnica


def filtrar_funcionarios(request):
    status = request.GET.get("status", "Ativo")
    qs = Funcionario.objects.filter(status=status).order_by("nome")

    if nome := request.GET.get("nome"):
        qs = qs.filter(nome__icontains=nome)

    if local_id := request.GET.get("local_trabalho"):
        try:
            local_obj = Departamentos.objects.get(id=local_id)
            qs = qs.filter(local_trabalho=local_obj)
        except Departamentos.DoesNotExist:
            pass

    if responsavel := request.GET.get("responsavel"):
        qs = qs.filter(responsavel_id=responsavel) if responsavel != "None" else qs.filter(responsavel__isnull=True)

    if escolaridade := request.GET.get("escolaridade"):
        qs = qs.filter(escolaridade=escolaridade)

    return qs


def obter_contexto_funcionario(funcionarios, status, page_obj):
    local_mais_comum = (
        Funcionario.objects.values("local_trabalho")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )

    return {
        "page_obj": page_obj,
        "departamentos": Departamentos.objects.filter(ativo=True).order_by("nome"),
        "responsaveis": Funcionario.objects.filter(responsavel__isnull=False, status="Ativo").distinct(),
        "niveis_escolaridade": Funcionario.objects.filter(status="Ativo").values_list("escolaridade", flat=True).distinct(),
        "status_opcoes": Funcionario.objects.values_list("status", flat=True).distinct(),
        "filtro_status": status,
        "total_ativos": Funcionario.objects.filter(status="Ativo").count(),
        "total_inativos": Funcionario.objects.filter(status="Inativo").count(),
        "total_pendentes": Funcionario.objects.filter(Q(curriculo__isnull=True) | Q(curriculo="")).count(),
        "local_mais_comum": local_mais_comum["local_trabalho"] if local_mais_comum else "N/A",
        "funcionarios": funcionarios,
        "funcionarios_paginados": page_obj,
    }


def montar_estrutura_organograma(funcionario):
    # ✅ data “aware” de acordo com TIME_ZONE do Django
    today = timezone.localdate()

    def calcular_prazo(lista, dias):
        for a in lista:
            if getattr(a, "data_avaliacao", None):
                data_limite = a.data_avaliacao + timedelta(days=dias)
                a.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"

    return {
        "funcionario": funcionario,
        "treinamentos": Treinamento.objects.filter(funcionarios=funcionario),
        "listas_presenca": ListaPresenca.objects.filter(participantes=funcionario),
        "avaliacoes_treinamento": AvaliacaoTreinamento.objects.filter(funcionario=funcionario),
        "avaliacoes_experiencia": list(AvaliacaoExperiencia.objects.filter(funcionario=funcionario)),
        "avaliacoes_anual": list(AvaliacaoAnual.objects.filter(funcionario=funcionario)),
        "job_rotations": JobRotationEvaluation.objects.filter(funcionario=funcionario),
        "equipamentos": TabelaTecnica.objects.filter(responsavel=funcionario),
        "integracao": IntegracaoFuncionario.objects.filter(funcionario=funcionario).last(),
    }


def gerar_mensagem_acesso_texto(funcionario):
    username = funcionario.user.username if funcionario.user else "NÃO CADASTRADO"
    email = funcionario.user.email if funcionario.user else "Não cadastrado"
    link = "https://sib.brasmol.com.br/"
    senha = "Bras@2025"
    video_senha = "https://www.canva.com/design/DAGpUXuwVGg/0jFy_0s06DOnZdXJDWQPDQ/watch"
    video_colab = "https://www.canva.com/design/DAGpUpGtN0s/KypajNUS2msIsvqPpNP26w/watch"
    video_gestor = "https://www.canva.com/design/DAGpUYf4ndI/cZFuSgjjpiXGvJkCqrQkKg/watch"

    is_gestor = Funcionario.objects.filter(responsavel_id=funcionario.id, status="Ativo").exists()
    video_modulo = video_gestor if is_gestor else video_colab

    return f"""
📢 Acesso ao Sistema – SIB Bras-Mol

Olá, {funcionario.nome} 👋

Segue abaixo os seus dados de acesso ao sistema da Qualidade Bras-Mol:

🌐 Link de Acesso: {link}
👤 Usuário (Login): {username} (Primeira Letra em maiúsculo)
🔑 Senha Padrão: {senha}

⚠️ Atenção:
✅ Ao acessar pela primeira vez, é obrigatório alterar sua senha.
➡️ Na tela de login, clique em “Esqueci minha senha / Alterar Senha”.
Um e-mail para redefinição de senha será enviado para: {email} ✉️

🎥 Vídeos de Apoio:

1️⃣ Como Redefinir sua Senha:
👉 {video_senha}

2️⃣ Conheça os Módulos Disponíveis no Sistema:
👉 {video_modulo}
"""


def gerar_organograma_dict(funcionario):
    subordinados = Funcionario.objects.filter(responsavel_id=funcionario.id, status="Ativo")
    estrutura = []
    for sub in subordinados:
        estrutura.append({
            "nome": sub.nome,
            "cargo": sub.cargo_atual,
            "foto": sub.foto.url if sub.foto else None,
            "subordinados": gerar_organograma_dict(sub),
            "quantidade_subordinados": subordinados.count(),
        })
    return estrutura


def gerar_cargos_para_impressao():
    funcionarios = Funcionario.objects.select_related("cargo_atual", "responsavel__cargo_atual")

    cargos_dict = {}
    subordinados_por_cargo = defaultdict(set)

    for f in funcionarios:
        if f.cargo_atual:
            nome = f.cargo_atual.nome
            cargos_dict[nome] = f.cargo_atual.id
            if f.responsavel and f.responsavel.cargo_atual:
                subordinados_por_cargo[f.responsavel.cargo_atual.nome].add(nome)

    cargos_nos = {
        nome: {"id": cid, "cargo": nome, "subordinados": []}
        for nome, cid in cargos_dict.items()
    }

    for responsavel, lista in subordinados_por_cargo.items():
        if responsavel in cargos_nos:
            cargos_nos[responsavel]["subordinados"] = [
                deepcopy(cargos_nos[n]) for n in lista if n in cargos_nos
            ]

    todos_subordinados = {n for lista in subordinados_por_cargo.values() for n in lista}
    return [deepcopy(c) for nome, c in cargos_nos.items() if nome not in todos_subordinados]
