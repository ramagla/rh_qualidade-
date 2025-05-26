from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from portaria.models import EntradaVisitante
from datetime import datetime

@login_required
@permission_required("portaria.view_entradavisitante", raise_exception=True)
def relatorio_visitantes(request):
    entradas = EntradaVisitante.objects.select_related("pessoa").order_by("-data", "-hora_entrada")

    # Filtros
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    nome = request.GET.get("nome")
    empresa = request.GET.get("empresa")
    pessoa_visitada = request.GET.get("pessoa_visitada")

    if data_inicio:
        entradas = entradas.filter(data__gte=data_inicio)
    if data_fim:
        entradas = entradas.filter(data__lte=data_fim)
    if nome:
        entradas = entradas.filter(pessoa__nome=nome)
    if empresa:
        entradas = entradas.filter(pessoa__empresa=empresa)
    if pessoa_visitada:
        entradas = entradas.filter(falar_com=pessoa_visitada)

    # Cálculo da permanência (hh:mm)
    for entrada in entradas:
        if entrada.hora_entrada and entrada.hora_saida:
            h_entrada = datetime.combine(entrada.data, entrada.hora_entrada)
            h_saida = datetime.combine(entrada.data, entrada.hora_saida)
            duracao = h_saida - h_entrada
            entrada.permanencia = str(duracao)[:-3]  # hh:mm
        else:
            entrada.permanencia = "-"

    # Valores únicos para filtros select2
    visitantes_disponiveis = (
        EntradaVisitante.objects
        .select_related("pessoa")
        .values_list("pessoa__nome", flat=True)
        .distinct()
        .order_by("pessoa__nome")
    )

    empresas_disponiveis = (
        EntradaVisitante.objects
        .select_related("pessoa")
        .exclude(pessoa__empresa__isnull=True)
        .exclude(pessoa__empresa__exact="")
        .values_list("pessoa__empresa", flat=True)
        .distinct()
        .order_by("pessoa__empresa")
    )

    pessoas_visitadas_disponiveis = (
        EntradaVisitante.objects
        .exclude(falar_com__isnull=True)
        .exclude(falar_com__exact="")
        .values_list("falar_com", flat=True)
        .distinct()
        .order_by("falar_com")
    )

    context = {
        "entradas": entradas,
        "data_inicio": data_inicio,
        "data_fim": data_fim,


        "nome": nome,
        "empresa": empresa,
        "pessoa_visitada": pessoa_visitada,
        "visitantes_disponiveis": visitantes_disponiveis,
        "empresas_disponiveis": empresas_disponiveis,
        "pessoas_visitadas_disponiveis": pessoas_visitadas_disponiveis,
    }

    return render(request, "relatorios/entrada_visitante_relatorio.html", context)

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from portaria.models import AtrasoSaida
from Funcionario.models import Funcionario
from django.db.models import Sum
from datetime import date
from datetime import timedelta


from datetime import datetime, date, time, timedelta
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from collections import defaultdict

@login_required
@permission_required("portaria.view_funcionario", raise_exception=True)
def relatorio_atrasos_saidas(request):
    nome = request.GET.get("nome")
    data_filtro = request.GET.get("data")
    tipo = request.GET.get("tipo")

    entrada_padrao = time(7, 0)
    saida_padrao = time(16, 48)
    tolerancia = timedelta(minutes=10)

    limite_atraso = (datetime.combine(date.today(), entrada_padrao) + tolerancia).time()
    limite_saida = (datetime.combine(date.today(), saida_padrao) - tolerancia).time()

    queryset = AtrasoSaida.objects.select_related("funcionario") \
        .exclude(tipo="hora_extra")

    if nome:
        queryset = queryset.filter(funcionario__nome=nome)
    if data_filtro:
        queryset = queryset.filter(data=data_filtro)

    eventos = []
    horas_por_funcionario = defaultdict(float)
    total_horas = 0  # ✅ somatório correto da coluna de horas

    for e in queryset:
        horas_diferenca = None
        h = e.horario

        if h:
            if e.tipo == "atraso" and h > limite_atraso:
                atraso = datetime.combine(date.min, h) - datetime.combine(date.min, limite_atraso)
                horas_diferenca = atraso.total_seconds() / 60
            elif e.tipo == "saida" and h < limite_saida:
                saida_antecipada = datetime.combine(date.min, limite_saida) - datetime.combine(date.min, h)
                horas_diferenca = saida_antecipada.total_seconds() / 60
                if h < time(12, 0):  # desconto almoço
                    horas_diferenca -= 60
                horas_diferenca = max(horas_diferenca, 0)
            else:
                continue
        else:
            continue

        if tipo and tipo != e.tipo:
            continue

        horas_por_funcionario[e.funcionario.nome] += horas_diferenca or 0
        total_horas += horas_diferenca or 0

        eventos.append({
            "obj": e,
            "tipo": e.tipo,
            "horas": horas_diferenca,
        })

    eventos.sort(key=lambda e: e["obj"].funcionario.nome)

    total_hoje = sum(1 for e in eventos if e["obj"].data == date.today())
    total_sem_justificativa = sum(1 for e in eventos if not e["obj"].observacao)

    nomes_disponiveis = Funcionario.objects.filter(status="Ativo").values_list("nome", flat=True).distinct()

    context = {
        "eventos": eventos,
        "nome": nome,
        "data": data_filtro,
        "tipo": tipo,
        "nomes_disponiveis": nomes_disponiveis,
        "total_hoje": total_hoje,
        "total_sem_justificativa": total_sem_justificativa,
        "total_horas": total_horas,  # ✅ correto agora
        "total_por_funcionario": dict(horas_por_funcionario),
        "horas_por_funcionario": dict(horas_por_funcionario),
    }

    return render(request, "relatorios/atraso_saida_relatorio.html", context)



from portaria.models import LigacaoPortaria

@login_required
@permission_required("portaria.view_ligacaoportaria", raise_exception=True)
def relatorio_ligacoes_recebidas(request):
    ligacoes = LigacaoPortaria.objects.select_related("falar_com").order_by("-data", "-horario")

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    pessoa_que_ligou = request.GET.get("pessoa_que_ligou")
    falar_com = request.GET.get("falar_com")

    if data_inicio:
        ligacoes = ligacoes.filter(data__gte=data_inicio)
    if data_fim:
        ligacoes = ligacoes.filter(data__lte=data_fim)
    if pessoa_que_ligou:
        ligacoes = ligacoes.filter(nome__icontains=pessoa_que_ligou)
    if falar_com:
        ligacoes = ligacoes.filter(falar_com__nome__icontains=falar_com)

    # Dados para Select2
    pessoas_que_ligaram = LigacaoPortaria.objects.values_list("nome", flat=True).distinct()
    colaboradores_disponiveis = LigacaoPortaria.objects.values_list("falar_com__nome", flat=True).distinct()

    context = {
        "ligacoes": ligacoes,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "pessoa_que_ligou": pessoa_que_ligou,
        "falar_com": falar_com,
        "pessoas_que_ligaram": pessoas_que_ligaram,
        "colaboradores_disponiveis": colaboradores_disponiveis,
    }

    return render(request, "relatorios/ligacoes_recebidas_relatorio.html", context)

from portaria.models import OcorrenciaPortaria

@login_required
@permission_required("portaria.view_ocorrenciaportaria", raise_exception=True)
def relatorio_ocorrencias(request):
    # ❌ NÃO usar select_related para campos não relacionais
    ocorrencias = OcorrenciaPortaria.objects.prefetch_related("pessoas_envolvidas").order_by("-data_inicio")

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo_ocorrencia")
    local = request.GET.get("local")

    if data_inicio:
        ocorrencias = ocorrencias.filter(data_inicio__date__gte=data_inicio)
    if data_fim:
        ocorrencias = ocorrencias.filter(data_inicio__date__lte=data_fim)
    if tipo:
        ocorrencias = ocorrencias.filter(tipo_ocorrencia=tipo)
    if local:
        ocorrencias = ocorrencias.filter(local__icontains=local)

    tipos_disponiveis = OcorrenciaPortaria.objects.values_list("tipo_ocorrencia", flat=True).distinct()
    locais_disponiveis = OcorrenciaPortaria.objects.values_list("local", flat=True).distinct()

    context = {
        "ocorrencias": ocorrencias,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "tipo": tipo,
        "local": local,
        "tipos_disponiveis": tipos_disponiveis,
        "locais_disponiveis": locais_disponiveis,
    }
    return render(request, "relatorios/ocorrencias_relatorio.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from portaria.models import RegistroConsumoAgua
from datetime import datetime
from django.db.models import Sum

@login_required
@permission_required("portaria.view_consumoagua", raise_exception=True)
def relatorio_consumo_agua(request):
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    consumos = RegistroConsumoAgua.objects.all().order_by("data")

    if data_inicio:
        consumos = consumos.filter(data__gte=data_inicio)
    if data_fim:
        consumos = consumos.filter(data__lte=data_fim)

    total_consumo = sum(
        (c.leitura_final or 0) - (c.leitura_inicial or 0)
        for c in consumos
    )

    # Preparar os dados para o gráfico
    labels = [c.data.strftime("%d/%m") for c in consumos]
    valores = [
        float((c.leitura_final or 0) - (c.leitura_inicial or 0))
        for c in consumos
    ]

    context = {
        "consumos": consumos,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "total_consumo": total_consumo,
        "labels": labels,
        "valores": valores,
    }
    return render(request, "relatorios/agua_relatorio.html", context)

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from datetime import date
from portaria.models import AtrasoSaida

@login_required
@permission_required("portaria.view_atrasosaida", raise_exception=True)
def relatorio_horas_extras(request):
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    colaborador = request.GET.get("colaborador")

    horas_extras = AtrasoSaida.objects.filter(tipo="hora_extra").select_related("funcionario").order_by("funcionario__nome")

    if data_inicio:
        horas_extras = horas_extras.filter(data__gte=data_inicio)
    if data_fim:
        horas_extras = horas_extras.filter(data__lte=data_fim)
    if colaborador:
        horas_extras = horas_extras.filter(funcionario_id=colaborador)

    # ⏱️ Total em segundos entre hora_fim e horario
    total_horas_segundos = sum(
        (
            (datetime.combine(datetime.min, h.hora_fim) - datetime.combine(datetime.min, h.horario)).total_seconds()
            if h.horario and h.hora_fim else 0
        )
        for h in horas_extras
    )

    total_horas_formatado = "{:02.0f}:{:02.0f}".format(
        total_horas_segundos // 3600,
        (total_horas_segundos % 3600) // 60
    )

    # 📊 Dados do gráfico
    agrupado = {}
    for h in horas_extras:
        if h.horario and h.hora_fim:
            nome = h.funcionario.nome
            segundos = (datetime.combine(datetime.min, h.hora_fim) - datetime.combine(datetime.min, h.horario)).total_seconds()
            agrupado[nome] = agrupado.get(nome, 0) + segundos

    grafico = {
        "labels": list(agrupado.keys()),
        "valores": [round(seg / 3600, 2) for seg in agrupado.values()]
    }

    colaboradores_qtd = len(set(h.funcionario_id for h in horas_extras if h.horario and h.hora_fim))
    total_por_colaborador = {
        nome: "{:02.0f}:{:02.0f}".format(segundos // 3600, (segundos % 3600) // 60)
        for nome, segundos in agrupado.items()
    }

    context = {
        "horas_extras": horas_extras,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "colaboradores": Funcionario.objects.filter(status="Ativo"),
        "colaborador_id": colaborador,
        "total_horas": total_horas_formatado,
        "colaboradores_qtd": colaboradores_qtd,
        "grafico": grafico,
        "total_por_colaborador": total_por_colaborador,

    }

    return render(request, "relatorios/horas_extras_relatorio.html", context)