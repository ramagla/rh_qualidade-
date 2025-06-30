# Django - Funcionalidades principais
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

# App Interno
from Funcionario.forms import FuncionarioForm
from Funcionario.models import Funcionario, HistoricoCargo
from Funcionario.models.cargo import Cargo
from Funcionario.utils.funcionario_utils import (
    filtrar_funcionarios,
    obter_contexto_funcionario,
    gerar_mensagem_acesso_texto,
    montar_estrutura_organograma,
)
from Funcionario.models import (    
    Treinamento,
)


@login_required
def lista_funcionarios(request):
    funcionarios = filtrar_funcionarios(request)
    paginator = Paginator(funcionarios, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    status = request.GET.get("status", "Ativo")
    context = obter_contexto_funcionario(funcionarios, status, page_obj)
    return render(request, "funcionarios/lista_funcionarios.html", context)


@login_required
def visualizar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    context = {"funcionario": funcionario, "now": timezone.now()}

    if funcionario.responsavel:
        responsavel = Funcionario.objects.filter(nome=funcionario.responsavel).first()
        context["cargo_responsavel"] = (
            responsavel.cargo_responsavel if responsavel else "Cargo não encontrado"
        )
    return render(request, "funcionarios/visualizar_funcionario.html", context)


@login_required
def cadastrar_funcionario(request):
    form = FuncionarioForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Funcionário cadastrado com sucesso!")
        return redirect("lista_funcionarios")
    return render(request, "funcionarios/form_funcionario.html", {"form": form})


@login_required
def editar_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    form = FuncionarioForm(request.POST or None, request.FILES or None, instance=funcionario)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Funcionário editado com sucesso!")
        return redirect("lista_funcionarios")

    responsaveis = Funcionario.objects.exclude(id=funcionario_id)
    return render(
        request,
        "funcionarios/form_funcionario.html",
        {"form": form, "funcionario": funcionario, "responsaveis": responsaveis},
    )


@login_required
def excluir_funcionario(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if Treinamento.objects.filter(funcionarios=funcionario).exists():
        funcionario.status = "Inativo"
        funcionario.save(update_fields=["status"])
        messages.success(request, "Funcionário foi marcado como Inativo.")
    else:
        funcionario.delete()
        messages.success(request, "Funcionário excluído com sucesso.")
    return redirect("lista_funcionarios")


class ImprimirFichaView(View):
    def get(self, request, funcionario_id):
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        context = montar_estrutura_organograma(funcionario)
        return render(request, "funcionarios/template_de_impressao.html", context)

    def post(self, request, funcionario_id):
        return self.get(request, funcionario_id)


@login_required
def listar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    historicos = HistoricoCargo.objects.filter(funcionario=funcionario).order_by("-data_atualizacao")
    return render(request, "funcionarios/historico_cargo.html", {"funcionario": funcionario, "historicos": historicos})


@login_required
def adicionar_historico_cargo(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    if request.method == "POST":
        cargo = get_object_or_404(Cargo, id=request.POST.get("cargo"))
        HistoricoCargo.objects.create(
            funcionario=funcionario,
            cargo=cargo,
            data_atualizacao=request.POST.get("data_atualizacao"),
        )
        messages.success(request, "Histórico de cargo adicionado com sucesso.")
        return redirect("listar_historico_cargo", funcionario_id=funcionario.id)
    cargos = Cargo.objects.all()
    return render(request, "funcionarios/adicionar_historico_cargo.html", {"funcionario": funcionario, "cargos": cargos})


@login_required
def excluir_historico_cargo(request, historico_id):
    historico = get_object_or_404(HistoricoCargo, id=historico_id)
    historico.delete()
    return redirect("listar_historico_cargo", funcionario_id=historico.funcionario.id)


@login_required
def gerar_mensagem_acesso(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    mensagem = gerar_mensagem_acesso_texto(funcionario)
    return render(request, "funcionarios/mensagem_acesso.html", {"mensagem": mensagem, "funcionario": funcionario})


@login_required
def selecionar_funcionario_mensagem_acesso(request):
    funcionarios = Funcionario.objects.filter(status="Ativo").order_by("nome")
    return render(request, "funcionarios/selecionar_mensagem_acesso.html", {"funcionarios": funcionarios})


@login_required
def gerar_mensagem_acesso_redirect(request):
    funcionario_id = request.GET.get("funcionario_id")
    if funcionario_id:
        return redirect("gerar_mensagem_acesso", funcionario_id=funcionario_id)
    return redirect("selecionar_funcionario_mensagem_acesso")
