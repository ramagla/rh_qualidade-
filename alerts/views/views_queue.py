# alerts/views_queue.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.conf import settings

import redis
import json
from rh_qualidade.celery import app as celery_app

# Helper para acesso ao Redis a partir do broker da CELERY_BROKER_URL
def _redis_from_broker():
    # Ex.: redis://localhost:6379/0  (conforme suas settings)
    url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
    # redis.from_url aceita o DSN diretamente
    return redis.from_url(url, decode_responses=True)

def _staff_check(user):
    return user.is_active and user.is_staff

@login_required
@user_passes_test(_staff_check)
def celery_dashboard(request):
    """
    Página HTML com status das filas e workers.
    Mostra:
      - Tamanho de listas Redis (ex.: 'emails', 'celery')
      - Workers ativos/ocupados (active/reserved/scheduled)
    """
    r = _redis_from_broker()

    # Filas que queremos observar (pode acrescentar outras se usar mais)
    filas_interesse = ["emails", "celery"]

    filas = []
    for q in filas_interesse:
        try:
            tamanho = r.llen(q)
        except Exception:
            tamanho = None
        filas.append({"nome": q, "tamanho": tamanho})

    # Inspeção dos workers
    i = celery_app.control.inspect()
    active = i.active() or {}
    reserved = i.reserved() or {}
    scheduled = i.scheduled() or {}
    registered = i.registered() or {}
    stats = i.stats() or {}

    contexto = {
        "filas": filas,
        "active": active,
        "reserved": reserved,
        "scheduled": scheduled,
        "registered": registered,
        "stats": stats,
    }
    return render(request, "alertas/celery_dashboard.html", contexto)

@login_required
@user_passes_test(_staff_check)
def celery_dashboard_json(request):
    """
    Endpoint JSON para auto-refresh do front (AJAX).
    """
    r = _redis_from_broker()
    filas_interesse = ["emails", "celery"]
    filas = []
    for q in filas_interesse:
        try:
            tamanho = r.llen(q)
        except Exception:
            tamanho = None
        filas.append({"nome": q, "tamanho": tamanho})

    i = celery_app.control.inspect()
    payload = {
        "filas": filas,
        "active": i.active() or {},
        "reserved": i.reserved() or {},
        "scheduled": i.scheduled() or {},
    }
    return JsonResponse(payload)

@login_required
@user_passes_test(_staff_check)
@require_POST
def celery_queue_purge(request):
    """
    Limpa uma fila específica (com cautela).
    Body: queue=<nome>
    """
    queue = request.POST.get("queue")
    if queue not in {"emails", "celery"}:
        return HttpResponseForbidden("Fila inválida.")

    r = _redis_from_broker()
    try:
        # esvazia list-type queue por LTRIM
        r.ltrim(queue, 1, 0)
    except Exception:
        pass
    return redirect("celery_dashboard")

# alerts/views_queue.py
from django.views.decorators.http import require_POST
from celery import signature

@login_required
@user_passes_test(_staff_check)
@require_POST
def celery_queue_run(request):
    """
    Força a execução imediata da primeira tarefa da fila.
    """
    queue = request.POST.get("queue")
    if queue not in {"emails", "celery"}:
        return HttpResponseForbidden("Fila inválida.")

    r = _redis_from_broker()
    try:
        raw = r.lpop(queue)
        if raw:
            # Mensagens da fila Celery são JSON codificados
            payload = json.loads(raw)
            body = payload.get("body")
            if body:
                task = signature(payload["headers"]["task"], args=payload["body"], kwargs={})
                task.apply_async(queue=queue)
    except Exception as e:
        print(f"[ERRO CELERY RUN] {e}")

    return redirect("celery_dashboard")

