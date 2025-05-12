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


# View para Permissões de Acesso
def permissoes_acesso(request):
    return render(request, "configuracoes/permissoes_acesso.html")


# View para Logs


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

from django.apps import apps
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
import json

from collections import defaultdict

from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages


def permissoes_acesso(request, usuario_id=None):
    usuario = get_object_or_404(User, id=usuario_id) if usuario_id else None

    # Processamento do formulário
    if request.method == "POST":
        user_id = request.POST.get("usuario_id")
        if not user_id:
            messages.error(request, "Usuário não selecionado.")
            return redirect("permissoes_acesso")

        user = get_object_or_404(User, pk=user_id)
        permissoes_ids = request.POST.getlist("permissoes")
        permissoes = Permission.objects.filter(id__in=permissoes_ids)

        user.user_permissions.set(permissoes)
        messages.success(
            request,
            f"Permissões atualizadas com sucesso para {user.get_full_name() or user.username}"
        )
        return redirect("permissoes_acesso", usuario_id=user.id)

    # Listas auxiliares
    usuarios = User.objects.all().order_by("username")
    grupos = Group.objects.all().order_by("name")

    # Agrupamento por app e modelo
    permissoes_agrupadas = defaultdict(lambda: defaultdict(list))
    permissoes = Permission.objects.select_related("content_type").order_by(
        "content_type__app_label", "content_type__model", "codename"
    )

    for perm in permissoes:
        app = perm.content_type.app_label
        modelo = perm.content_type.name.title()  # fallback seguro com nome visível
        permissoes_agrupadas[app][modelo].append(perm)

    context = {
        "usuarios": usuarios,
        "grupos": grupos,
        "usuario": usuario,
        "permissoes_agrupadas": dict(permissoes_agrupadas),
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
