import hashlib
from decimal import Decimal, InvalidOperation
from django.db import transaction
from comercial.api_client import BrasmolClient
from comercial.models.faturamento import FaturamentoRegistro
from comercial.models.clientes import Cliente
import re
from datetime import datetime, timedelta


def _parse_date_any(s):
    """
    Aceita 'dd/mm/yyyy' ou 'yyyy-mm-dd' e retorna date, ou None.
    """
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None


def _norm_code(s):
    """
    Remove pontuações e deixa maiúsculo para casar 'C35.001' com 'C35001'.
    """
    return re.sub(r"[^A-Za-z0-9]", "", (s or "")).upper() or None



def _as_decimal(v, q=4):
    """
    Converte valores (str/num) para Decimal com q casas.
    Retorna None quando vazio/inválido.
    """
    if v is None or v == "":
        return None
    try:
        return round(Decimal(str(v)), q)
    except (InvalidOperation, ValueError):
        return None


def _as_int(v):
    """
    Converte para inteiro de forma segura.
    Aceita strings numéricas e Decimals.
    Retorna None quando vazio/inválido.
    """
    if v is None or v == "":
        return None
    try:
        # Ex.: '10.0' -> 10 ; '10,0' -> 10
        s = str(v).strip().replace(",", ".")
        d = Decimal(s)
        return int(d.to_integral_value(rounding=None))
    except (InvalidOperation, ValueError):
        try:
            return int(v)
        except Exception:
            return None


def _to_str_upper(v):
    """
    Normaliza para string maiúscula ou None.
    """
    if v is None:
        return None
    s = str(v).strip()
    return s.upper() if s else None


def _hash_unico(nfe, cliente_codigo, cliente, ocorrencia, item_codigo, item_valor_unitario, item_qtd, valor_frete):
    """
    Chave idempotente por combinação de campos (inclui cliente_codigo).
    Usa os valores já normalizados.
    """
    base = (
        f"{nfe or ''}|{cliente_codigo or ''}|{cliente or ''}|{ocorrencia or ''}|"
        f"{item_codigo or ''}|{item_valor_unitario or ''}|{item_qtd or ''}|{valor_frete or ''}"
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _split_cliente(raw: str):
    """
    Aceita:
      'C35 - CORDOBA'  -> ('C35', 'CORDOBA')
      'C35- CORDOBA'   -> ('C35', 'CORDOBA')
      'C35 CORDOBA'    -> (None, 'C35 CORDOBA')  # sem separador padrão
    Se a API já mandar 'cod_cliente', priorizamos ele.
    """
    if not raw:
        return (None, None)
    m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*-\s*(.+)$", raw.strip())
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    return (None, raw.strip())


def _flatten_vendas(lista):
    """
    Transforma cada venda (com 'itens') em linhas 1:1 por item, replicando campos do cabeçalho.
    Se a API trouxer 'cod_cliente', utiliza-o; caso contrário tenta extrair de 'cliente' no formato 'COD - NOME'.
    """
    saida = []
    for v in lista:
        itens = v.get("itens") or []

        # Preferir cod_cliente vindo da API; fallback para split do campo 'cliente'
        cli_cod_api = v.get("cod_cliente")
        cli_nome_api = v.get("cliente")
        cod, nome = _split_cliente(cli_nome_api)
        cliente_codigo_raw = (cod or cli_cod_api)
        cliente_nome = nome if nome else cli_nome_api

        base = {
            "nfe": v.get("nfe"),
            "ocorrencia": v.get("ocorrencia"),
            "cliente_codigo": cliente_codigo_raw,  # será normalizado depois
            "cliente": cliente_nome,               # somente NOME (livre)
            "valor_frete": v.get("valor_frete"),
        }
        for it in itens:
            row = dict(base)
            row.update({
                "item_codigo": it.get("codigo"),
                "item_quantidade": it.get("quantidade"),
                "item_valor_unitario": it.get("valor_unitario"),
                "item_ipi": it.get("ipi"),
            })
            saida.append(row)
    return saida


def _extrair_lote(payload):
    """
    Normaliza o payload da GetVendas para uma lista de registros.
    Suporta:
      - lista direta
      - dict com lista em 'registros' ou 'data'
      - dict com registros em chaves numéricas '0','1',...
      - fallback: primeira lista encontrada no dict
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


def _iter_nf_periodo(client, data_inicio, data_fim, registros="500"):
    """
    Busca Notas Fiscais em janelas de 15 dias, com retry reduzindo 'registros'
    (ex.: 500 -> 200 -> 100 -> 50). Renderiza lotes já normalizados via _extrair_lote.
    """
    try:
        ini = _parse_date_any(data_inicio) or datetime.strptime(data_inicio, "%Y-%m-%d").date()
        fim = _parse_date_any(data_fim)    or datetime.strptime(data_fim, "%Y-%m-%d").date()
    except Exception:
        ini = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

    if ini > fim:
        ini, fim = fim, ini

    step = timedelta(days=15)
    cursor = ini
    while cursor <= fim:
        sub_ini = cursor
        sub_fim = min(cursor + step, fim)
        cursor = sub_fim + timedelta(days=1)

        # retries com tamanhos de página menores
        for reg_try in [int(registros), 200, 100, 50]:
            pagina_atual = 1
            falhou = False
            while True:
                params = {
                    "dataInicio": sub_ini.strftime("%Y-%m-%d"),
                    "dataFim": sub_fim.strftime("%Y-%m-%d"),
                    "tipo": "json",
                    "pagina": str(pagina_atual),
                    "registros": str(reg_try),
                }
                try:
                    payload = client.fetch_notas_fiscais(params)
                except Exception:
                    falhou = True
                    break

                lote = _extrair_lote(payload)
                if lote:
                    yield lote

                # Heurística de parada: vazio ou menor que page size
                if not lote or len(lote) < reg_try:
                    break
                pagina_atual += 1

            if not falhou:
                # terminou este sub-período com sucesso; vá para o próximo sub-período
                break
            # senão, tenta próximo reg_try menor



@transaction.atomic
def sincronizar_faturamento(data_inicio: str, data_fim: str, pagina="1", registros="500", sobrescrever: bool = False):
    """
    Busca na API GetVendas e insere/atualiza em FaturamentoRegistro.
    """
    client = BrasmolClient()
    acumulado = []

    pagina_atual = int(pagina or 1)
    total_paginas = None

    while True:
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "tipo": "json",
            "pagina": str(pagina_atual),
            "registros": str(registros),
        }
        payload = client.fetch_vendas(params)

        if isinstance(payload, dict) and total_paginas is None:
            tp = payload.get("total_paginas")
            try:
                total_paginas = int(tp) if tp is not None else None
            except (TypeError, ValueError):
                total_paginas = None

        lote = _extrair_lote(payload)
        acumulado.extend(lote)

        if total_paginas is not None:
            if pagina_atual >= total_paginas:
                break
            pagina_atual += 1
        else:
            if not lote or len(lote) < int(registros):
                break
            pagina_atual += 1

    linhas = _flatten_vendas(acumulado)

    ins = upd = skip = 0
    for d in linhas:
        # Cabeçalho
        nfe = (d.get("nfe") or None)
        ocorrencia = d.get("ocorrencia")

        # Normalizações
        cliente_codigo = _to_str_upper(d.get("cliente_codigo"))  # evita UPPER(integer)
        cliente = d.get("cliente")  # nome livre
        valor_frete = _as_decimal(d.get("valor_frete"), q=2)

        # Item (normaliza código para evitar duplicidade por caixa)
        codigo = _to_str_upper(d.get("item_codigo"))
        quantidade = _as_int(d.get("item_quantidade"))           # IntegerField no model
        valor_unitario = _as_decimal(d.get("item_valor_unitario"), q=4)
        ipi = _as_decimal(d.get("item_ipi"), q=2)

        # Vincula cliente (cod_bm) com segurança
        cliente_obj = None
        if cliente_codigo:
            cliente_obj = (
                Cliente.objects
                .filter(cod_bm__isnull=False)
                .filter(cod_bm__iexact=cliente_codigo)
                .first()
            )

        # Chave idempotente com valores normalizados
        chave = _hash_unico(
            nfe, cliente_codigo, cliente, ocorrencia, codigo, valor_unitario, quantidade, valor_frete
        )

        if not sobrescrever:
            # Somente inserir: se já existe, pula
            _, created = FaturamentoRegistro.objects.get_or_create(
                chave_unica=chave,
                defaults={
                    "nfe": nfe,
                    "ocorrencia": ocorrencia,
                    "cliente_codigo": cliente_codigo,
                    "cliente": cliente,
                    "valor_frete": valor_frete,
                    "item_codigo": codigo,
                    "item_quantidade": quantidade,
                    "item_valor_unitario": valor_unitario,
                    "item_ipi": ipi,
                    "cliente_vinculado": cliente_obj,
                }
            )
            if created:
                ins += 1
            else:
                skip += 1
            continue

        # Modo sobrescrever: atualiza se existir e não estiver congelado
        obj = FaturamentoRegistro.objects.filter(chave_unica=chave).first()
        if obj:
            is_frozen = getattr(obj, "congelado", False)  # funciona mesmo sem o campo existir
            if is_frozen:
                skip += 1
                continue

            fields = {
                "nfe": nfe,
                "ocorrencia": ocorrencia,
                "cliente_codigo": cliente_codigo,
                "cliente": cliente,
                "valor_frete": valor_frete,
                "item_codigo": codigo,
                "item_quantidade": quantidade,
                "item_valor_unitario": valor_unitario,
                "item_ipi": ipi,
                "cliente_vinculado": cliente_obj,
            }

            alterou = False
            for k, v in fields.items():
                if getattr(obj, k) != v:
                    setattr(obj, k, v)
                    alterou = True

            if alterou:
                obj.save(update_fields=list(fields.keys()))
                upd += 1
            else:
                skip += 1
        else:
            FaturamentoRegistro.objects.create(
                chave_unica=chave,
                nfe=nfe,
                ocorrencia=ocorrencia,
                cliente_codigo=cliente_codigo,
                cliente=cliente,
                valor_frete=valor_frete,
                item_codigo=codigo,
                item_quantidade=quantidade,
                item_valor_unitario=valor_unitario,
                item_ipi=ipi,
                cliente_vinculado=cliente_obj,
            )
            ins += 1

    # ---- Segunda fase: buscar Notas Fiscais e atualizar perc_icms por item ----
    datas_oc = []
    for d in linhas:
        dt = _parse_date_any(d.get("ocorrencia"))
        if dt:
            datas_oc.append(dt)

    if datas_oc:
        nf_ini = min(datas_oc) - timedelta(days=5)
        nf_fim = max(datas_oc) + timedelta(days=5)
    else:
        # fallback: parâmetros informados
        nf_ini = _parse_date_any(data_inicio) or datetime.strptime(data_inicio, "%Y-%m-%d").date()
        nf_fim = _parse_date_any(data_fim)    or datetime.strptime(data_fim, "%Y-%m-%d").date()

    nf_acumulado = []
    for nf_lote in _iter_nf_periodo(
        client,
        nf_ini.strftime("%Y-%m-%d"),
        nf_fim.strftime("%Y-%m-%d"),
        registros=registros,
    ):
        nf_acumulado.extend(nf_lote)

    # Monta índice: (numero NF, COD_PRODUTO upper) -> perc_icms
    icms_map = {}
    for nf in nf_acumulado:
        numero_nf = str(nf.get("numero") or "").strip()
        itens = nf.get("itens") or []
        for it in itens:
            cod = _norm_code(it.get("cod_produto"))
            if not numero_nf or not cod:
                continue
            perc = it.get("perc_icms")
            if perc is None and isinstance(it.get("icms"), dict):
                perc = it["icms"].get("aliquota")
            icms_map[(numero_nf, cod)] = _as_decimal(perc, q=2)


    # Aplica no banco: atualiza somente se mudou (respeita 'congelado')
    if icms_map:
        qs = FaturamentoRegistro.objects.filter(nfe__in=[k[0] for k in icms_map.keys()])
        for r in qs.only("id", "nfe", "item_codigo", "perc_icms", "congelado"):
            if getattr(r, "congelado", False):
                continue
            chave = (str(r.nfe or "").strip(), _norm_code(r.item_codigo))
            novo_icms = icms_map.get(chave)

            if novo_icms is None:
                continue
            if r.perc_icms != novo_icms:
                r.perc_icms = novo_icms
                r.save(update_fields=["perc_icms"])
                upd += 1  # conta como atualização também

    return ins, upd, skip
