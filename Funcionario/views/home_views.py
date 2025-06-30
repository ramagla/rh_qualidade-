# Bibliotecas padrão
from datetime import datetime

# Django
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

# App Interno
from Funcionario.forms import EventoForm
from Funcionario.models import Evento, Settings, AtualizacaoSistema
from Funcionario.utils.dashboard_utils import (
    obter_contexto_home,
    obter_eventos_json,
    obter_calendario_feriados,
    gerar_arquivo_ics,
    obter_contexto_impressao_cipa,
    obter_contexto_impressao_brigada
)



@login_required
def home(request):
    """Renderiza a página inicial com dados analíticos e gráficos."""
    context = obter_contexto_home()
    context["form"] = EventoForm()
    return render(request, "dashboard/home.html", context)


@login_required
def sucesso_view(request):
    """Renderiza página de sucesso genérica."""
    return render(request, "sucesso.html")


def login_view(request):
    """Realiza autenticação do usuário."""
    settings = Settings.objects.first()
    versoes_concluidas = AtualizacaoSistema.objects.filter(status="concluido")

    ultima_atualizacao = sorted(
        versoes_concluidas,
        key=lambda x: (x.data_termino, x.versao),
        reverse=True
    )[0] if versoes_concluidas else None

    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect("home_geral")
        return render(request, "login.html", {
            "settings": settings,
            "ano_atual": datetime.now().year,
            "versao": ultima_atualizacao.versao if ultima_atualizacao else "0.0.0",
            "erro": "Usuário ou senha inválidos.",
        })

    return render(request, "login.html", {
        "settings": settings,
        "ano_atual": datetime.now().year,
        "versao": ultima_atualizacao.versao if ultima_atualizacao else "0.0.0",
    })


@login_required
def calendario_view(request):
    """Renderiza o calendário anual com eventos e feriados."""
    ano = request.GET.get("ano", datetime.now().year)
    eventos, feriados = obter_eventos_json(ano)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"eventos": eventos, "feriados": feriados}, safe=False)

    return render(request, "calendario/calendario.html", {
        "eventos_json": eventos,
        "feriados_json": feriados,
        "ano": ano
    })


@csrf_exempt
@login_required
def adicionar_evento(request):
    """Adiciona um novo evento ao calendário."""
    if request.method == "POST":
        try:
            Evento.objects.create(
                titulo=request.POST.get("titulo"),
                data_inicio=datetime.strptime(request.POST.get("data_inicio"), "%Y-%m-%dT%H:%M"),
                data_fim=datetime.strptime(request.POST.get("data_fim"), "%Y-%m-%dT%H:%M"),
                cor=request.POST.get("cor"),
            )
            return JsonResponse({"status": "Evento criado com sucesso!"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@login_required
def excluir_evento(request, evento_id):
    """Exclui um evento do calendário."""
    evento = get_object_or_404(Evento, id=evento_id)
    evento.delete()
    return JsonResponse({"status": "Evento excluído com sucesso!"})


@csrf_exempt
@login_required
def editar_evento(request, evento_id):
    """Edita um evento existente."""
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == "POST":
        evento.titulo = request.POST.get("titulo")
        evento.data_inicio = datetime.strptime(request.POST.get("data_inicio"), "%Y-%m-%dT%H:%M")
        evento.data_fim = datetime.strptime(request.POST.get("data_fim"), "%Y-%m-%dT%H:%M")
        evento.cor = request.POST.get("cor")
        evento.save()
        return JsonResponse({"status": "Evento atualizado com sucesso!"})
    return JsonResponse({"error": "Erro ao atualizar o evento"}, status=400)


@login_required
def imprimir_calendario(request):
    """Renderiza o calendário para impressão com feriados e eventos."""
    ano = request.GET.get("ano", "2024")
    eventos = obter_calendario_feriados(ano)
    return render(request, "calendario/imprimir_calendario.html", {
        "eventos": eventos,
        "ano": ano,
        "anos_disponiveis": [2023, 2024, 2025, 2026]
    })


@login_required
def exportar_calendario(request):
    """Exporta o calendário como arquivo ICS."""
    return gerar_arquivo_ics()


@login_required
def eventos_json(request):
    """Retorna eventos e feriados em formato JSON."""
    ano = request.GET.get("ano", datetime.now().year)
    eventos, feriados = obter_eventos_json(ano)
    return JsonResponse({"eventos": eventos, "feriados": feriados})


@login_required
def marcar_alertas_como_lidos(request):
    """Marca todos os alertas não lidos como lidos."""
    request.user.alertas.filter(lido=False).update(lido=True)
    return JsonResponse({"status": "ok"})


@login_required
def imprimir_cipa_view(request):
    """Renderiza o template de impressão dos representantes da CIPA."""
    context = obter_contexto_impressao_cipa()
    return render(request, 'dashboard/impressao_cipa.html', context)


@login_required
def imprimir_brigada_view(request):
    """Renderiza o template de impressão dos brigadistas."""
    context = obter_contexto_impressao_brigada()
    return render(request, 'dashboard/impressao_brigada.html', context)
