from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from metrologia.forms.CalibracaoDispositivoForm import CalibracaoDispositivoForm
from metrologia.models import Afericao, CalibracaoDispositivo, Cota, Dispositivo
from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required("metrologia.view_calibracaodispositivo", raise_exception=True)
def lista_calibracoes_dispositivos(request):
    dispositivos = Dispositivo.objects.all()
    # Filtros
    codigo_dispositivo = request.GET.get("codigo_dispositivo", "")
    instrumento_utilizado = request.GET.get("instrumento_utilizado", "")
    status = request.GET.get("status", "")
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")

    # Query inicial com prefetch para otimizar aferições e cotas
    calibracoes = CalibracaoDispositivo.objects.prefetch_related(
        "afericoes__cota"
    ).all()

    # Aplicando filtros
    if codigo_dispositivo:
        calibracoes = calibracoes.filter(codigo_dispositivo__codigo=codigo_dispositivo)
    if instrumento_utilizado:
        calibracoes = calibracoes.filter(
            instrumento_utilizado__nome_equipamento=instrumento_utilizado
        )
    if status:
        calibracoes = calibracoes.filter(status=status)
    if data_inicio:
        calibracoes = calibracoes.filter(data_afericao__gte=data_inicio)
    if data_fim:
        calibracoes = calibracoes.filter(data_afericao__lte=data_fim)

    # Atualiza status geral com base nas aferições
    for calibracao in calibracoes:
        afericoes = calibracao.afericoes.all()
        calibracao.status = (
            "Aprovado"
            if all(afericao.status == "Aprovado" for afericao in afericoes)
            else "Reprovado"
        )

    # Contagem para os cards
    total_calibracoes = calibracoes.count()
    total_aprovadas = calibracoes.filter(status="Aprovado").count()
    total_reprovadas = calibracoes.filter(status="Reprovado").count()

    # Dados únicos para os filtros baseados na lista de calibrações
    codigos = calibracoes.values_list(
        "codigo_dispositivo__codigo", flat=True
    ).distinct()
    instrumentos = calibracoes.values_list(
        "instrumento_utilizado__nome_equipamento", flat=True
    ).distinct()

    context = {
        "page_obj": Paginator(calibracoes, 10).get_page(request.GET.get("page")),
        "codigos": codigos,
        "instrumentos": instrumentos,
        "total_calibracoes": total_calibracoes,
        "total_aprovadas": total_aprovadas,
        "total_reprovadas": total_reprovadas,
        "dispositivos": dispositivos,
    }

    return render(request, "calibracoes/lista_calibracoes_dispositivos.html", context)


@login_required
def salvar_calibracao_dispositivo(request, pk=None):
    if pk:
        calibracao = get_object_or_404(CalibracaoDispositivo, pk=pk)
        titulo = "Editar Calibração de Dispositivo"
        edicao = True
    else:
        calibracao = None
        titulo = "Cadastrar Calibração de Dispositivo"
        edicao = False

    if request.method == "POST":
        form = CalibracaoDispositivoForm(request.POST, instance=calibracao)

        if form.is_valid():
            try:
                calibracao_dispositivo = form.save()

                for key, value in request.POST.items():
                    if key.startswith("afericoes["):
                        cota_numero = key.split("[")[1].split("]")[0]
                        if not cota_numero.isdigit():
                            raise ValueError(f"Número da cota inválido: {cota_numero}")
                        cota = Cota.objects.filter(
                            numero=cota_numero,
                            dispositivo=calibracao_dispositivo.codigo_dispositivo,
                        ).first()
                        if not cota:
                            raise Http404(f"Cota {cota_numero} não encontrada.")

                        valor = float(value.replace(",", ".")) if value else None
                        if valor is not None:
                            Afericao.objects.update_or_create(
                                calibracao_dispositivo=calibracao_dispositivo,
                                cota=cota,
                                defaults={"valor": valor}
                            )

                calibracao_dispositivo.atualizar_status()

                msg = "Calibração atualizada com sucesso!" if pk else "Calibração cadastrada com sucesso!"
                messages.success(request, msg)
                return redirect("lista_calibracoes_dispositivos")

            except Exception as e:
                messages.error(request, f"Erro ao processar calibração: {e}")
        else:
            messages.error(request, "Erro no formulário. Verifique os campos.")
    else:
        form = CalibracaoDispositivoForm(instance=calibracao)

    dispositivo = calibracao.codigo_dispositivo if calibracao else None
    codigo_peca = dispositivo.codigo[:-2] if dispositivo and len(dispositivo.codigo) > 2 else ""
    desenho_url = dispositivo.desenho_anexo.url if dispositivo and dispositivo.desenho_anexo else None
    afericoes = calibracao.afericoes.all() if calibracao else []

    context = {
        "form": form,
        "calibracao": calibracao,
        "titulo_pagina": titulo,
        "codigo_peca": codigo_peca,
        "desenho_url": desenho_url,
        "afericoes": afericoes,
        "edicao": edicao,
        "url_voltar": "lista_calibracoes_dispositivos",
        "param_id": None,
    }
    return render(request, "calibracoes/form_calibracao_dispositivo.html", context)


@login_required
@permission_required("metrologia.add_calibracaodispositivo", raise_exception=True)
def cadastrar_calibracao_dispositivo(request):
    return salvar_calibracao_dispositivo(request)



@csrf_exempt
def get_dispositivo_info(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    cotas = Cota.objects.filter(dispositivo=dispositivo)

    # Tenta identificar a calibração atual (modo edição)
    afericoes_dict = {}
    calibracao_id = request.GET.get("calibracao_id")
    if calibracao_id:
        afericoes = Afericao.objects.filter(calibracao_dispositivo_id=calibracao_id)
        afericoes_dict = {str(a.cota.numero): float(a.valor) for a in afericoes}

    cotas_data = []
    for cota in cotas:
        cotas_data.append({
            "numero": cota.numero,
            "valor_minimo": float(cota.valor_minimo),
            "valor_maximo": float(cota.valor_maximo),
            "valor_aferido": afericoes_dict.get(str(cota.numero))
        })

    return JsonResponse({
        "codigo_peca": dispositivo.codigo[:-2] if len(dispositivo.codigo) > 2 else dispositivo.codigo,
        "desenho_url": dispositivo.desenho_anexo.url if dispositivo.desenho_anexo else None,
        "cotas": cotas_data
    })

@login_required
@permission_required("metrologia.change_calibracaodispositivo", raise_exception=True)
def editar_calibracao_dispositivo(request, pk):
    return salvar_calibracao_dispositivo(request, pk=pk)


@login_required
@permission_required("metrologia.delete_calibracaodispositivo", raise_exception=True)
def excluir_calibracao_dispositivo(request, id):
    calibracao = get_object_or_404(CalibracaoDispositivo, id=id)
    if request.method == "POST":
        calibracao.delete()
        messages.success(request, "Calibração excluída com sucesso.")
        return redirect("calibracoes_dispositivos")

    return render(
        request,
        "calibracoes/excluir_calibracao_dispositivo.html",
        {"calibracao": calibracao},
    )

@login_required
@permission_required("metrologia.imprimir_calibracao_dispositivo", raise_exception=True)
def imprimir_calibracao_dispositivo(request, dispositivo_id):
    calibracoes = CalibracaoDispositivo.objects.filter(
        codigo_dispositivo_id=dispositivo_id
    ).order_by("-data_afericao")

    if not calibracoes.exists():
        messages.warning(
            request, "Nenhuma calibração encontrada para este dispositivo."
        )
        return redirect("lista_calibracoes_dispositivos")

    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

    return render(
        request,
        "calibracoes/imprimir_calibracao_dispositivo.html",
        {"calibracoes": calibracoes, "dispositivo": dispositivo},
    )
