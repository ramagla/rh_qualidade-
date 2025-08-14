from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.http import require_GET
from comercial.api_client import BrasmolClient
from datetime import datetime


def _parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "sim", "yes"}


def _extrair_lote(payload):
    """
    Normaliza o payload da GetVendas para uma lista de registros.
    Suporta:
      - lista direta
      - dict com lista em 'registros' ou 'data'
      - dict com registros nas chaves numéricas '0','1',...
      - fallback: primeira lista encontrada
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        # 1) listas padrão
        for k in ("registros", "data"):
            v = payload.get(k)
            if isinstance(v, list):
                return v

        # 2) chaves numéricas "0","1",...
        numericas = [k for k in payload.keys() if str(k).isdigit()]
        numericas.sort(key=lambda s: int(s))
        lote = [payload[k] for k in numericas if isinstance(payload.get(k), dict)]
        if lote:
            return lote

        # 3) fallback: primeira lista encontrada
        for v in payload.values():
            if isinstance(v, list):
                return v

    return []


def _flatten_vendas(lista):
    """
    Transforma cada venda em múltiplas linhas (1 por item),
    replicando os campos do cabeçalho em cada item.
    """
    saida = []
    for v in lista:
        itens = v.get("itens") or []
        base = {k: v.get(k) for k in (
            "registro", "negociacao", "venda", "valor", "nfe", "ocorrencia",
            "emissor_fiscal", "cod_cliente", "cliente", "nome_vendedor",
            "cod_tranport", "nome_transp", "valor_frete", "quantidade",
            "especie", "numero", "marca", "peso_bruto", "peso_liquido"
        )}
        for it in itens:
            row = dict(base)
            row.update({
                "item_codigo": it.get("codigo"),
                "item_descricao": it.get("descricao"),
                "item_quantidade": it.get("quantidade"),
                "item_valor_unitario": it.get("valor_unitario"),
                "item_ipi": it.get("ipi"),
                "item_previsao_entrega": it.get("previsao_entrega"),
            })
            saida.append(row)
    return saida


@require_GET
def get_vendas(request):
    """
    GET /api/getVendas
    Autorização: header 'apikey' OU querystring 'apikey'
    Parâmetros: dataInicio, dataFim, pagina, registros, tipo=json, todos, flatten
    """
    # 1) Autorização
    apikey = (request.headers.get("apikey") or request.GET.get("apikey") or "").strip()
    chave_valida = (getattr(settings, "BRASMOL_API_KEY", "") or "").strip()
    if not apikey or apikey != chave_valida:
        return HttpResponseForbidden("API key inválida.")

    # 2) Parâmetros
    data_inicio = request.GET.get("dataInicio")
    data_fim    = request.GET.get("dataFim")
    try:
        pagina    = int(request.GET.get("pagina", "1") or "1")
        registros = int(request.GET.get("registros", "200") or "200")
    except ValueError:
        return HttpResponseBadRequest("Parâmetros 'pagina' e 'registros' devem ser inteiros.")
    tipo        = request.GET.get("tipo", "json")
    todos       = _parse_bool(request.GET.get("todos"), default=False)
    flatten     = _parse_bool(request.GET.get("flatten"), default=False)

    if not data_inicio or not data_fim:
        return HttpResponseBadRequest("Parâmetros obrigatórios: dataInicio, dataFim.")

    # 3) Validação de data (YYYY-MM-DD)
    for d in (data_inicio, data_fim):
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            return HttpResponseBadRequest("Datas devem estar no formato YYYY-MM-DD.")

    # 4) Chamada à API externa
    client = BrasmolClient()
    acumulado = []
    pagina_atual = pagina
    total_paginas = None

    while True:
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "tipo": tipo,
            "pagina": str(pagina_atual),
            "registros": str(registros),
        }
        payload = client.fetch_vendas(params=params)

        # tentar ler total_paginas (quando houver)
        if isinstance(payload, dict) and total_paginas is None:
            tp = payload.get("total_paginas")
            try:
                total_paginas = int(tp) if tp is not None else None
            except (TypeError, ValueError):
                total_paginas = None

        lote = _extrair_lote(payload)
        acumulado.extend(lote)

        if not todos:
            break

        # paginação com total_paginas ou por heurística de tamanho do lote
        if total_paginas is not None:
            if pagina_atual >= total_paginas:
                break
            pagina_atual += 1
        else:
            if not lote or len(lote) < registros:
                break
            pagina_atual += 1

    # 5) Resposta
    saida = _flatten_vendas(acumulado) if flatten else acumulado
    return JsonResponse(saida, safe=False)

@require_GET
def get_notas_fiscais(request):
    """
    GET /api/getNotasFiscais
    Autorização: header 'apikey' OU querystring 'apikey'
    Parâmetros: dataInicio, dataFim, pagina, registros, tipo=json, todos, flatten
    - Quando flatten=1, retorna linhas por item: numero (NF), cod_produto, perc_icms
    """
    # 1) Autorização
    apikey = (request.headers.get("apikey") or request.GET.get("apikey") or "").strip()
    chave_valida = (getattr(settings, "BRASMOL_API_KEY", "") or "").strip()
    if not apikey or apikey != chave_valida:
        return HttpResponseForbidden("API key inválida.")

    # 2) Parâmetros
    data_inicio = request.GET.get("dataInicio")
    data_fim    = request.GET.get("dataFim")
    try:
        pagina    = int(request.GET.get("pagina", "1") or "1")
        registros = int(request.GET.get("registros", "200") or "200")
    except ValueError:
        return HttpResponseBadRequest("Parâmetros 'pagina' e 'registros' devem ser inteiros.")
    tipo        = request.GET.get("tipo", "json")
    todos       = _parse_bool(request.GET.get("todos"), default=False)
    flatten     = _parse_bool(request.GET.get("flatten"), default=False)

    if not data_inicio or not data_fim:
        return HttpResponseBadRequest("Parâmetros obrigatórios: dataInicio, dataFim.")

    # 3) Validação de data (YYYY-MM-DD)
    for d in (data_inicio, data_fim):
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            return HttpResponseBadRequest("Datas devem estar no formato YYYY-MM-DD.")

    # 4) Chamada à API externa
    client = BrasmolClient()
    acumulado = []
    pagina_atual = pagina
    total_paginas = None

    while True:
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "tipo": tipo,
            "pagina": str(pagina_atual),
            "registros": str(registros),
        }
        payload = client.fetch_notas_fiscais(params=params)

        # tentar ler total_paginas (quando houver)
        if isinstance(payload, dict) and total_paginas is None:
            tp = payload.get("total_paginas")
            try:
                total_paginas = int(tp) if tp is not None else None
            except (TypeError, ValueError):
                total_paginas = None

        lote = _extrair_lote(payload)
        acumulado.extend(lote)

        if not todos:
            break

        if total_paginas is not None:
            if pagina_atual >= total_paginas:
                break
            pagina_atual += 1
        else:
            if not lote or len(lote) < registros:
                break
            pagina_atual += 1

    if not flatten:
        return JsonResponse(acumulado, safe=False)

    # Flatten (uma linha por item)
    saida = []
    for nf in acumulado:
        numero_nf = nf.get("numero")
        itens = nf.get("itens") or []
        for it in itens:
            saida.append({
                "numero": numero_nf,
                "cod_produto": it.get("cod_produto"),
                "perc_icms": it.get("perc_icms"),
            })
    return JsonResponse(saida, safe=False)