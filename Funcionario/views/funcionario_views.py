from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import View

from Funcionario.forms import FuncionarioForm
from Funcionario.models import (
    AvaliacaoAnual,
    AvaliacaoExperiencia,
    Funcionario,
    HistoricoCargo,
    Treinamento,
)
from Funcionario.models.avaliacao_treinamento import AvaliacaoTreinamento
from Funcionario.models.integracao_funcionario import IntegracaoFuncionario
from Funcionario.models.job_rotation_evaluation import JobRotationEvaluation
from Funcionario.models.lista_presenca import ListaPresenca
from Funcionario.models.choices_departamento import DEPARTAMENTOS_EMPRESA

from ..models.cargo import Cargo


def is_authenticated(user):
    return user.is_authenticated


@login_required
def lista_funcionarios(request):
    # Aplica o filtro padrão de status "Ativo"
    status = request.GET.get("status", "Ativo")  # Valor padrão é "Ativo"
    funcionarios = Funcionario.objects.filter(status=status).order_by("nome")

    # Dados para os cards
    total_ativos = Funcionario.objects.filter(status="Ativo").count()
    total_inativos = Funcionario.objects.filter(status="Inativo").count()
    local_mais_comum = (
        Funcionario.objects.values("local_trabalho")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )
    total_pendentes = Funcionario.objects.filter(
        Q(curriculo__isnull=True) | Q(curriculo="")
    ).count()  # Verifica NULL e strings vazias

    # Lista de responsáveis disponíveis
    responsaveis = Funcionario.objects.filter(
        responsavel__isnull=False, status="Ativo"
    ).distinct()

    # Outros filtros
    nome = request.GET.get("nome")
    if nome:
        funcionarios = funcionarios.filter(nome__icontains=nome)

    local_trabalho = request.GET.get("local_trabalho")
    if local_trabalho:
        funcionarios = funcionarios.filter(local_trabalho=local_trabalho)

    responsavel = request.GET.get("responsavel")
    if responsavel:
        if responsavel == "None":
            funcionarios = funcionarios.filter(responsavel__isnull=True)
        else:
            funcionarios = funcionarios.filter(responsavel_id=responsavel)

    escolaridade = request.GET.get("escolaridade")
    if escolaridade:
        funcionarios = funcionarios.filter(escolaridade=escolaridade)

    # Paginação
    paginator = Paginator(funcionarios, 10)  # 10 itens por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "departamentos_choices": DEPARTAMENTOS_EMPRESA,
        "responsaveis": responsaveis,
        "niveis_escolaridade": Funcionario.objects.filter(status="Ativo")
        .values_list("escolaridade", flat=True)
        .distinct(),
        "status_opcoes": Funcionario.objects.values_list(
            "status", flat=True
        ).distinct(),
        "filtro_status": status,  # Inclui o status aplicado no contexto
        "total_ativos": total_ativos,
        "total_pendentes": total_pendentes,
        "local_mais_comum": (
            local_mais_comum["local_trabalho"] if local_mais_comum else "N/A"
        ),
        "total_inativos": total_inativos,
        "funcionarios": funcionarios,  # Apenas funcionários filtrados
        "funcionarios_paginados": page_obj,
    }

    return render(request, "funcionarios/lista_funcionarios.html", context)


@login_required
def visualizar_funcionario(request, funcionario_id):
    # Busca o colaborador ou retorna 404
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Obter o cargo do responsável, caso exista
    cargo_responsavel = None
    if funcionario.responsavel:
        responsaveis = Funcionario.objects.filter(nome=funcionario.responsavel)
        if responsaveis.exists():
            cargo_responsavel = responsaveis.first().cargo_responsavel
        else:
            cargo_responsavel = "Cargo não encontrado"

    # Monta o contexto, incluindo a data/hora atual
    context = {
        "funcionario": funcionario,
        "cargo_responsavel": cargo_responsavel,
        "now": timezone.now(),
    }

    # Renderiza o template de visualização
    return render(
        request,
        "funcionarios/visualizar_funcionario.html",
        context
    )

@login_required
def cadastrar_funcionario(request):
    if request.method == "POST":
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save(commit=False)
            print(
                f"Responsável: {funcionario.responsavel}, Cargo do Responsável: {funcionario.cargo_responsavel}"
            )
            funcionario.save()
            messages.success(request, "Funcionário cadastrado com sucesso!")
            return redirect("lista_funcionarios")
        else:
            messages.error(
                request,
                "Erro ao cadastrar o funcionário. Verifique os dados e tente novamente.",
            )
    else:
        form = FuncionarioForm()
    return render(request, "funcionarios/form_funcionario.html", {"form": form})


@login_required
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Inicialize as variáveis
    cargo_responsavel = None
    responsavel_nome = funcionario.responsavel  # Nome do responsável

    # Verifique se o responsável foi fornecido
    if responsavel_nome:
        try:
            # Busque o funcionário responsável pelo nome
            responsavel_funcionario = Funcionario.objects.get(nome=responsavel_nome)
            cargo_responsavel = (
                responsavel_funcionario.cargo_responsavel
            )  # Acesse o cargo do responsável
        except Funcionario.DoesNotExist:
            cargo_responsavel = "Cargo não encontrado"  # Ou lidar de outra forma

    # Criação do formulário para edição
    form = FuncionarioForm(
        request.POST or None, request.FILES or None, instance=funcionario
    )

    if request.method == "POST":
        print("Formulário submetido")
        if form.is_valid():
            print("Formulário válido")
            form.save()
            messages.success(request, "Funcionário editado com sucesso!")
            return redirect("lista_funcionarios")
        else:
            print("Erros no formulário:", form.errors)

    # Certifique-se de que 'responsaveis' está sendo passado no contexto
    # Excluir o próprio funcionário da lista
    responsaveis = Funcionario.objects.exclude(id=funcionario_id)

    context = {
        "form": form,
        "funcionario": funcionario,
        "cargo_responsavel": cargo_responsavel,
        "responsaveis": responsaveis,  # Adicione isso ao contexto
    }

    return render(request, "funcionarios/form_funcionario.html", context)


@login_required
def excluir_funcionario(request, funcionario_id):
    # Busca o colaborador ou retorna 404
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Se houver treinamentos vinculados, inativa em vez de excluir
    if Treinamento.objects.filter(funcionarios=funcionario).exists():
        funcionario.status = "Inativo"
        funcionario.save(update_fields=["status"])
        messages.success(
            request,
            "Funcionário possui registros associados e foi marcado como Inativo."
        )
    else:
        # Caso contrário, exclui de fato
        funcionario.delete()
        messages.success(request, "Funcionário excluído com sucesso.")

    return redirect("lista_funcionarios")


from django.views import View
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta


from metrologia.models import TabelaTecnica


class ImprimirFichaView(View):
    def get(self, request, funcionario_id):
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)

        # Dados relacionados
        treinamentos = Treinamento.objects.filter(funcionarios=funcionario)
        listas_presenca = ListaPresenca.objects.filter(participantes=funcionario)
        avaliacoes_treinamento = AvaliacaoTreinamento.objects.filter(funcionario=funcionario)
        avaliacoes_experiencia = AvaliacaoExperiencia.objects.filter(funcionario=funcionario)
        avaliacoes_anual = AvaliacaoAnual.objects.filter(funcionario=funcionario)
        job_rotations = JobRotationEvaluation.objects.filter(funcionario=funcionario)
        equipamentos = TabelaTecnica.objects.filter(responsavel=funcionario)
        integracao = IntegracaoFuncionario.objects.filter(funcionario=funcionario).last()

        # Status de prazo para avaliações
        today = timezone.now().date()
        for avaliacao in avaliacoes_experiencia:
            data_limite = avaliacao.data_avaliacao + timedelta(days=30)
            avaliacao.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"

        for avaliacao in avaliacoes_anual:
            data_limite = avaliacao.data_avaliacao + timedelta(days=365)
            avaliacao.get_status_prazo = "Dentro do Prazo" if data_limite >= today else "Em Atraso"

        context = {
            "funcionario": funcionario,
            "treinamentos": treinamentos,
            "listas_presenca": listas_presenca,
            "avaliacoes_treinamento": avaliacoes_treinamento,
            "avaliacoes_experiencia": avaliacoes_experiencia,
            "avaliacoes_anual": avaliacoes_anual,
            "job_rotations": job_rotations,
            "equipamentos": equipamentos,
            "integracao": integracao,
        }

        return render(request, "funcionarios/template_de_impressao.html", context)

    def post(self, request, funcionario_id):
        return self.get(request, funcionario_id)


def gerar_organograma(funcionario):
    """
    Função recursiva para construir a hierarquia completa.
    Inclui a contagem de subordinados.
    """
    subordinados = Funcionario.objects.filter(
        responsavel_id=funcionario.id, status="Ativo"
    )
    estrutura = []
    for subordinado in subordinados:
        estrutura.append(
            {
                "nome": subordinado.nome,
                "cargo": subordinado.cargo_atual,
                "foto": subordinado.foto.url if subordinado.foto else None,
                "subordinados": gerar_organograma(subordinado),
                "quantidade_subordinados": subordinados.count(),
            }
        )
    return estrutura


@login_required
def organograma_view(request):
    print(f"Usuário autenticado: {request.user}")  # Verifica o usuário autenticado
    # Confirmação do tipo do objeto
    print(f"Tipo de request.user: {type(request.user)}")

    # Se o usuário for um superuser, ele pode ver todos os funcionários
    if request.user.is_superuser:
        top_funcionarios = Funcionario.objects.filter(
            responsavel__isnull=True, status="Ativo"
        )
    else:
        # Tenta encontrar um funcionário correspondente ao usuário autenticado
        funcionario = Funcionario.objects.filter(
            nome=request.user.get_full_name()
        ).first()

        if funcionario:
            top_funcionarios = Funcionario.objects.filter(
                responsavel=funcionario, status="Ativo"
            )
        else:
            # Se não encontrar, mostra todos os funcionários no topo da hierarquia
            top_funcionarios = Funcionario.objects.filter(
                responsavel__isnull=True, status="Ativo"
            )

    organograma = []
    for funcionario in top_funcionarios:
        organograma.append(
            {
                "nome": funcionario.nome,
                "cargo": funcionario.cargo_atual,
                "foto": funcionario.foto.url if funcionario.foto else None,
                "subordinados": gerar_organograma(funcionario),
            }
        )

    return render(
        request, "funcionarios/organograma/organograma.html", {"organograma": organograma}
    )


# Listar histórico de cargos
@login_required
def listar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    historicos = HistoricoCargo.objects.filter(funcionario=funcionario).order_by(
        "-data_atualizacao"
    )
    return render(
        request,
        "funcionarios/historico_cargo.html",
        {"funcionario": funcionario, "historicos": historicos},
    )


@login_required
def adicionar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if request.method == "POST":
        cargo_id = request.POST.get("cargo")
        data_atualizacao = request.POST.get(
            "data_atualizacao"
        )  # Captura a data do formulário
        cargo = get_object_or_404(Cargo, id=cargo_id)

        HistoricoCargo.objects.create(
            funcionario=funcionario,
            cargo=cargo,
            data_atualizacao=data_atualizacao,  # Usa a data fornecida pelo usuário
        )
        messages.success(request, "Histórico de cargo adicionado com sucesso.")
        return redirect("listar_historico_cargo", funcionario_id=funcionario.id)

    cargos = Cargo.objects.all()
    return render(
        request,
        "funcionarios/adicionar_historico_cargo.html",
        {"funcionario": funcionario, "cargos": cargos},
    )


@login_required
def excluir_historico_cargo(request, historico_id):
    # Obtém o objeto HistoricoCargo
    historico = get_object_or_404(HistoricoCargo, id=historico_id)

    if request.method == "POST":
        # Exclui o histórico
        historico.delete()
        # Redireciona após a exclusão
        return redirect(
            "listar_historico_cargo", funcionario_id=historico.funcionario.id
        )

    return redirect("listar_historico_cargo", funcionario_id=historico.funcionario.id)

from collections import defaultdict
from datetime import date

from collections import defaultdict
from django.db.models import Prefetch


def montar_organograma(lista):
    mapa = {}
    raiz = []

    for item in lista:
        item['subordinados'] = []
        mapa[item['id']] = item

    for item in lista:
        pai_id = item.get('responsavel_id')
        if pai_id and pai_id in mapa:
            mapa[pai_id]['subordinados'].append(item)
        else:
            raiz.append(item)

    return raiz

from collections import defaultdict
from copy import deepcopy

@login_required
def imprimir_organograma(request):
    funcionarios = Funcionario.objects.select_related("cargo_atual", "responsavel__cargo_atual")

    cargos_dict = {}
    subordinados_por_cargo = defaultdict(set)

    for f in funcionarios:
        if f.cargo_atual:
            cargo_nome = f.cargo_atual.nome
            cargos_dict[cargo_nome] = f.cargo_atual.id

            if f.responsavel and f.responsavel.cargo_atual:
                responsavel_nome = f.responsavel.cargo_atual.nome
                subordinados_por_cargo[responsavel_nome].add(cargo_nome)

    # Cria os nós únicos (sem vínculo ainda)
    cargos_nos = {
        nome: {
            'id': id,
            'cargo': nome,
            'subordinados': []
        }
        for nome, id in cargos_dict.items()
    }

    # Relaciona subordinados (usando cópia para evitar ciclos)
    for responsavel_nome, lista in subordinados_por_cargo.items():
        if responsavel_nome in cargos_nos:
            cargos_nos[responsavel_nome]['subordinados'] = [
                deepcopy(cargos_nos[nome]) for nome in lista if nome in cargos_nos
            ]

    # Detecta cargos sem responsáveis (topo)
    todos_subordinados = {nome for lista in subordinados_por_cargo.values() for nome in lista}
    topo = [deepcopy(n) for nome, n in cargos_nos.items() if nome not in todos_subordinados]

    contexto = {
        'organograma': topo,
        'revisao': '06',
        'data': '04/03/2025',
        'elaborador': 'Anderson Goveia',
        'aprovador': 'Lilian Fernandes'
    }
    return render(request, 'funcionarios/organograma/organograma_imprimir.html', contexto)