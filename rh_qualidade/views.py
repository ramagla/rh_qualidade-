import json
from datetime import datetime
import math

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


from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.shortcuts import get_object_or_404, redirect, render


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

    # 🔃 Carregar permissões especiais antes do POST
    acesso_modulos = Permission.objects.filter(codename__startswith="acesso_").order_by("name")

    # Processar POST
    if request.method == "POST":
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

    # Agrupar todas as permissões por app e modelo
    permissoes_agrupadas = defaultdict(lambda: defaultdict(list))
    todas = Permission.objects.select_related("content_type").order_by(
        "content_type__app_label", "content_type__model", "codename"
    )
    for perm in todas:
        app = perm.content_type.app_label
        modelo = perm.content_type.name.title()
        permissoes_agrupadas[app][modelo].append(perm)

    # Permissões ativas (somente diretas, por ID)
    permissoes_efetivas = set()
    if usuario:
        permissoes_efetivas = set(usuario.user_permissions.values_list("id", flat=True))

    if grupo:
        permissoes_efetivas = set(grupo.permissions.values_list("id", flat=True))

    context = {
        "usuarios": User.objects.order_by("username"),
        "grupos": Group.objects.order_by("name"),
        "usuario": usuario,
        "grupo": grupo,
        "permissoes_agrupadas": {app: dict(modelos) for app, modelos in permissoes_agrupadas.items()},
        "permissoes_ativas_usuario": permissoes_efetivas,
        "acesso_modulos": acesso_modulos,
    }

    return render(request, "configuracoes/permissoes_acesso.html", context)

@login_required
def copiar_permissoes(request):
    if request.method == "POST":
        origem_id = request.POST.get("usuario_origem_id")
        destino_id = request.POST.get("usuario_destino_id")

        if origem_id == destino_id:
            messages.warning(request, "Você não pode copiar permissões para o mesmo usuário.")
            return redirect("permissoes_acesso")

        usuario_origem = get_object_or_404(User, pk=origem_id)
        usuario_destino = get_object_or_404(User, pk=destino_id)

        # Pega apenas as permissões diretas (não as de grupo)
        permissoes_origem = usuario_origem.user_permissions.all()

        # Apaga permissões anteriores (opcional — ou pode usar `.add()` se quiser manter)
        usuario_destino.user_permissions.add(*permissoes_origem)

        messages.success(
            request,
            f"Permissões copiadas de {usuario_origem.get_full_name() or usuario_origem.username} para {usuario_destino.get_full_name() or usuario_destino.username}."
        )
        return redirect(f"/permissoes-acesso/?usuario_id={usuario_destino.id}")

    messages.error(request, "Requisição inválida.")
    return redirect("permissoes_acesso")








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
from alerts.models import AlertaUsuario

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from datetime import datetime
from Funcionario.models import Funcionario, Comunicado, AtualizacaoSistema, Settings
from alerts.models import AlertaUsuario
from portaria.models.ocorrencia import OcorrenciaPortaria  # ✅ necessário
from Funcionario.models import Funcionario, BancoHoras
from django.db.models import Sum

from django.contrib.sessions.models import Session
from django.utils.timezone import now as timezone_now

@login_required
def home_geral(request):
    # 🎂 Aniversariantes
    aniversariantes = Funcionario.objects.filter(
        status="Ativo", 
        data_nascimento__month=now().month
    )

    # 👥 Total de colaboradores logados no sistema
    # 👥 Total de colaboradores logados no sistema

    # Primeiro: limpa sessões expiradas
    Session.objects.filter(expire_date__lt=timezone_now()).delete()

    # Agora busca sessões ativas
    active_sessions = Session.objects.filter(expire_date__gte=timezone_now())
    uid_list = []

    for session in active_sessions:
        data = session.get_decoded()
        uid = data.get('_auth_user_id')
        if uid:
            uid_list.append(uid)

    total_colaboradores = Funcionario.objects.filter(user__id__in=uid_list, status="Ativo").count()


    # 📢 Últimos comunicados
    comunicados = Comunicado.objects.order_by("-data")[:4]

    # ⚙️ Última atualização
    ultima_atualizacao_concluida = AtualizacaoSistema.objects.filter(status="concluido").order_by("-data_termino").first()

    proximas_atualizacoes = AtualizacaoSistema.objects.filter(status="em_andamento").order_by("previsao")

    historico_versoes = AtualizacaoSistema.objects.filter(status="concluido").exclude(
        id=ultima_atualizacao_concluida.id if ultima_atualizacao_concluida else None
    ).order_by("-data_termino")

    data_atualizacao_formatada = None
    if ultima_atualizacao_concluida and ultima_atualizacao_concluida.data_termino:
        data = ultima_atualizacao_concluida.data_termino
        data_atualizacao_formatada = data.strftime("%d/%m/%Y %H:%M") if isinstance(data, datetime) else data.strftime("%d/%m/%Y")

    # 📨 Recados
    recados_usuario = AlertaUsuario.objects.filter(
        usuario=request.user,
        tipo="recado"
    ).order_by("-criado_em")[:4]

    # 🔔 Outros alertas
    alertas_raw = AlertaUsuario.objects.filter(
        usuario=request.user
    ).exclude(tipo="recado").order_by("-criado_em")[:4]

    alertas_usuario = []
    for alerta in alertas_raw:
        ocorrencia = None
        if alerta.tipo == "ocorrencia" and alerta.referencia_id:
            try:
                ocorrencia = OcorrenciaPortaria.objects.get(pk=alerta.referencia_id)
            except OcorrenciaPortaria.DoesNotExist:
                pass
        alertas_usuario.append({
            "titulo": alerta.titulo,
            "mensagem": alerta.mensagem,
            "criado_em": alerta.criado_em,
            "ocorrencia": ocorrencia,
        })

    # ⚙️ Configuração geral
    settings = Settings.objects.first()

    # 🕓 Saldo de banco de horas do usuário logado
    funcionario = getattr(request.user, 'funcionario', None)
    saldo_funcionario = None
    total_dias_funcionario = 0  # ✅ garantir que sempre exista
    subordinados_com_saldo = []

    if funcionario:
        total = BancoHoras.objects.filter(funcionario=funcionario).aggregate(
            saldo_total=Sum('horas_trabalhadas')
        )['saldo_total']
        if total:
            saldo_funcionario = total.total_seconds() / 3600
            total_minutos = saldo_funcionario * 60
            total_dias_funcionario = math.floor(abs(total_minutos) / 453)
            if saldo_funcionario < 0:
                total_dias_funcionario = -total_dias_funcionario


        # Subordinados diretos
        subordinados = Funcionario.objects.filter(responsavel=funcionario, status="Ativo")

        # Para cada subordinado, calcula o saldo
        for sub in subordinados:
            saldo_sub = BancoHoras.objects.filter(funcionario=sub).aggregate(
                saldo_total=Sum('horas_trabalhadas')
            )['saldo_total']

            saldo_sub_horas = saldo_sub.total_seconds() / 3600 if saldo_sub else 0
            saldo_sub_minutos = saldo_sub_horas * 60
            saldo_sub_dias = math.floor(abs(saldo_sub_minutos) / 453)
            if saldo_sub_horas < 0:
                saldo_sub_dias = -saldo_sub_dias

            subordinados_com_saldo.append({
                "nome": sub.nome,
                "foto": sub.foto.url if sub.foto else None,
                "saldo": saldo_sub_horas,
                "dias": saldo_sub_dias
            })


            

    context = {
        "aniversariantes": aniversariantes,
        "total_colaboradores": total_colaboradores,
        "comunicados": comunicados,
        "recados_usuario": recados_usuario,
        "alertas_usuario": alertas_usuario,
        "ultima_atualizacao_concluida": ultima_atualizacao_concluida,
        "proximas_atualizacoes": proximas_atualizacoes,
        "historico_versoes": historico_versoes,
        "data_atualizacao_formatada": data_atualizacao_formatada,
        "settings": settings,
        "saldo_funcionario": saldo_funcionario,
        "subordinados_com_saldo": subordinados_com_saldo,
        "total_dias_funcionario": total_dias_funcionario,

    }


    return render(request, "home_geral.html", context)


from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils.timezone import now as timezone_now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def usuarios_ativos(request):
    # Primeiro: limpa sessões já expiradas (não precisa mais de cron se fizer isso aqui)
    Session.objects.filter(expire_date__lt=timezone_now()).delete()

    # Agora busca apenas sessões ativas
    active_sessions = Session.objects.filter(expire_date__gte=timezone_now())
    user_ids = []

    for session in active_sessions:
        data = session.get_decoded()
        uid = data.get('_auth_user_id')
        if uid:
            user_ids.append(uid)

    usuarios = User.objects.filter(id__in=user_ids).order_by('username')

    return render(request, 'configuracoes/usuarios_ativos.html', {'usuarios': usuarios})


from django.http import HttpResponse
from django.template.loader import render_to_string

def pwa_manifest(request):
    content = render_to_string("manifest.webmanifest", {})
    return HttpResponse(content, content_type="application/manifest+json")

def pwa_service_worker(request):
    content = render_to_string("service-worker.js", {})
    return HttpResponse(content, content_type="application/javascript")

