import json
from datetime import datetime

import requests
from django.apps import apps
from django.contrib.auth.models import Permission, User
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_str


def acesso_negado(request):
    current_time = datetime.now()
    return render(
        request,
        "acesso_negado.html",
        {"user": request.user, "current_time": current_time},
    )




def logs(request):
    return render(request, "configuracoes/logs.html")


# View para Alertas de E-mails


def alertas_emails(request):
    return render(request, "configuracoes/alertas_emails.html")


# View para Feriados


def feriados(request):
    # Usando a API de Feriados para obter dados
    try:
        response = requests.get("https://brasilapi.com.br/api/feriados/v1/2025")
        feriados = response.json()
    except Exception as e:
        feriados = []
    return render(request, "configuracoes/feriados.html", {"feriados": feriados})

# views.py

from django.contrib.auth.models import User, Group, Permission
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from collections import defaultdict


@login_required
def permissoes_acesso(request):
    usuario = None
    grupo = None

    user_id = request.GET.get("usuario_id") or request.POST.get("usuario_id")
    grupo_id = request.GET.get("grupo_id") or request.POST.get("grupo_id")

    # Selecionar alvo
    if user_id:
        usuario = get_object_or_404(User, pk=user_id)
    elif grupo_id:
        grupo = get_object_or_404(Group, pk=grupo_id)

    # 🔃 Carregar permissões especiais ANTES do POST
    acesso_modulos = Permission.objects.filter(codename__startswith="acesso_").order_by("name")

    # Processar POST
    if request.method == "POST":
        print("🧾 POST bruto:", dict(request.POST))
        print("🧾 getlist permissoes:", request.POST.getlist("permissoes"))
        print("🧾 getlist permissoes[]:", request.POST.getlist("permissoes[]"))
        permissoes_ids = request.POST.getlist("permissoes")
        permissoes = Permission.objects.filter(id__in=permissoes_ids)

        if usuario:
            usuario.user_permissions.set(permissoes)
            messages.success(request, f"Permissões atualizadas para {usuario.get_full_name() or usuario.username}")
            return redirect(f"{request.path}?usuario_id={usuario.id}")

        if grupo:
            grupo.permissions.set(permissoes)
            messages.success(request, f"Permissões atualizadas para o grupo {grupo.name}")
            return redirect(f"{request.path}?grupo_id={grupo.id}")


    # Agrupar permissões para exibição
    permissoes_agrupadas = defaultdict(lambda: defaultdict(list))
    todas = Permission.objects.select_related("content_type").order_by(
        "content_type__app_label", "content_type__model", "codename"
    )
    for perm in todas:
        app = perm.content_type.app_label
        modelo = perm.content_type.name.title()
        permissoes_agrupadas[app][modelo].append(perm)

    # Permissões efetivas
    permissoes_efetivas = set()
    permissoes_diretas = set()

    if usuario:
        permissoes_efetivas = {
            f"{p.content_type.app_label.lower()}.{p.codename}"
            for p in Permission.objects.filter(user=usuario) | Permission.objects.filter(group__user=usuario)
        }
        permissoes_diretas = {
            f"{p.content_type.app_label.lower()}.{p.codename}"
            for p in usuario.user_permissions.all()
        }

    if grupo:
        permissoes_efetivas = {
            f"{p.content_type.app_label.lower()}.{p.codename}"
            for p in grupo.permissions.all()
        }

    context = {
        "usuarios": User.objects.order_by("username"),
        "grupos": Group.objects.order_by("name"),
        "usuario": usuario,
        "grupo": grupo,
        "permissoes_agrupadas": {app: dict(modelos) for app, modelos in permissoes_agrupadas.items()},
        "permissoes_ativas_usuario": permissoes_efetivas,
        "permissoes_diretas_usuario": permissoes_diretas,
        "acesso_modulos": acesso_modulos,
    }

    return render(request, "configuracoes/permissoes_acesso.html", context)









import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.timezone import now
from django.conf import settings

# Modelos importados (pegos dos seus arquivos __init__.py)
from Funcionario.models import (
    AtualizacaoSistema, AvaliacaoAnual, AvaliacaoExperiencia, AvaliacaoTreinamento,
    Cargo, Revisao, Comunicado, Documento, RevisaoDoc, Evento, Funcionario, 
    HistoricoCargo, IntegracaoFuncionario, JobRotationEvaluation, ListaPresenca, 
    Atividade, MatrizPolivalencia, Nota, Settings, Treinamento
)

from metrologia.models import (
    Calibracao, Afericao, CalibracaoDispositivo,
    ControleEntradaSaida, Cota, Dispositivo, TabelaTecnica
)

# Configuração do Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

@csrf_exempt
def chat_gpt_query(request):
    print("➡️ Endpoint /chat-gpt/ foi chamado")

    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido. Use POST.'}, status=405)

    user_question = request.POST.get('question')
    print("📝 Pergunta recebida:", user_question)

    if not user_question:
        return JsonResponse({'error': 'Pergunta não fornecida!'}, status=400)

    # Regras específicas de consulta no banco (exemplo)
    try:
        if 'quantos comunicados' in user_question.lower():
            qtd = Comunicado.objects.count()
            resposta = f"Atualmente, você tem {qtd} comunicados cadastrados no sistema."
            print("📊 Resposta do banco:", resposta)
            return JsonResponse({'answer': resposta})

        if 'quantos funcionários' in user_question.lower():
            qtd = Funcionario.objects.count()
            resposta = f"Existem {qtd} funcionários cadastrados no sistema."
            return JsonResponse({'answer': resposta})

        if 'calibração vencida' in user_question.lower():
            today = now().date()
            equipamentos = TabelaTecnica.objects.filter(data_ultima_calibracao__lt=today)
            dados = [
                f"{equip.nome_equipamento} (Vencimento: {equip.data_ultima_calibracao.strftime('%d/%m/%Y')})"
                for equip in equipamentos
            ]
            resposta = (
                f"Equipamentos com calibração vencida:\n" + "\n".join(dados)
                if dados else "Não há equipamentos com calibração vencida no momento."
            )
            return JsonResponse({'answer': resposta})

        # Exemplo de resposta dinâmica com contexto
        print(f"⚙️ Enviando para Gemini com contexto: {user_question}")

        context = """
        Você é um assistente de RH e Metrologia da empresa Bras-mol.
        Utilize o contexto para responder perguntas relacionadas aos dados disponíveis no sistema.
        Tabelas disponíveis:
        - Comunicado: comunicação interna.
        - Funcionario: dados de colaboradores.
        - Treinamento: cursos e capacitações.
        - Avaliação Anual e de Experiência: desempenho de funcionários.
        - Matriz de Polivalência: habilidades dos colaboradores.
        - Tabela Técnica: dispositivos e equipamentos da metrologia.
        """

        # Adicionando histórico fictício para melhor contextualização
        chat_session = model.start_chat(history=[
            {
                "role": "user",
                "parts": [context]
            },
            {
                "role": "model",
                "parts": ["Ok! Pronto para responder perguntas sobre o sistema."]
            }
        ])

        response = chat_session.send_message(user_question)
        chat_response = response.text
        print("🟢 Resposta Gemini:", chat_response)

        return JsonResponse({'answer': chat_response})

    except Exception as e:
        print("❌ Erro inesperado:", str(e))
        return JsonResponse({'error': f'Erro inesperado: {str(e)}'}, status=500)



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from datetime import datetime
from Funcionario.models import Funcionario, Comunicado, AtualizacaoSistema, Settings

@login_required
def home_geral(request):
    # 📆 Aniversariantes do mês
    aniversariantes = Funcionario.objects.filter(
        status="Ativo",
        data_nascimento__month=now().month
    )

    # 👥 Total de colaboradores ativos
    total_colaboradores = Funcionario.objects.filter(status="Ativo").count()

    # 📣 Últimos comunicados
    comunicados = Comunicado.objects.order_by("-data")[:4]

    # 🔧 Última atualização concluída do sistema
    ultima_atualizacao = AtualizacaoSistema.objects.filter(
        status="concluido"
    ).order_by("-data_termino").first()

    # Formatação segura da data
    data_atualizacao_formatada = None
    if ultima_atualizacao and ultima_atualizacao.data_termino:
        if isinstance(ultima_atualizacao.data_termino, datetime):
            data_atualizacao_formatada = ultima_atualizacao.data_termino.strftime("%d/%m/%Y %H:%M")
        else:
            data_atualizacao_formatada = ultima_atualizacao.data_termino.strftime("%d/%m/%Y")

    settings = Settings.objects.first()

    context = {
        "aniversariantes": aniversariantes,
        "total_colaboradores": total_colaboradores,
        "comunicados": comunicados,
        "ultima_atualizacao": ultima_atualizacao,
        "data_atualizacao_formatada": data_atualizacao_formatada,
        "settings": settings,
    }

    return render(request, "home_geral.html", context)
