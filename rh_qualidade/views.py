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


def permissoes_acesso(request, usuario_id=None):
    usuario = get_object_or_404(User, id=usuario_id) if usuario_id else request.user

    permissoes_json = []
    modulos = apps.get_app_configs()

    for modulo in modulos:
        permissoes = Permission.objects.filter(content_type__app_label=modulo.label)
        permissoes_lista = [
            {
                "id": p.id,
                "text": force_str(p.name),
                "ativo": usuario.has_perm(f"{p.content_type.app_label}.{p.codename}"),
            }
            for p in permissoes
        ]
        if permissoes_lista:
            permissoes_json.append(
                {"text": force_str(modulo.verbose_name), "nodes": permissoes_lista}
            )

    # Depuração: Exibir JSON gerado no terminal do servidor
    print(
        "🔹 JSON de permissões:",
        json.dumps(permissoes_json, indent=4, ensure_ascii=False),
    )

    context = {
        "usuarios_permissoes_json": json.dumps(permissoes_json, ensure_ascii=False),
        "usuario": usuario,
    }

    return render(request, "configuracoes/permissoes_acesso.html", context)
