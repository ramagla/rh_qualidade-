import re
import hashlib
from time import sleep
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction

from comercial.api_client import BrasmolClient
from comercial.models.clientes import Cliente
from comercial.models.faturamento import (
    FaturamentoRegistro,
    FaturamentoDuplicata,
)

# =========================
# Config / Debug helpers
# =========================

DEBUG_ICMS = True  # deixe True para logar; mude para False para silenciar

def _dbg(*args):
    if DEBUG_ICMS:
        print("[SYNC-ICMS]", *args)

ICMS_DEFAULT_BY_UF = getattr(
    settings,
    "ICMS_DEFAULT_BY_UF",
    {
        "SP": Decimal("18.00"),
        "RJ": Decimal("20.00"),
        "MG": Decimal("18.00"),
        "ES": Decimal("17.00"),
        "PR": Decimal("19.00"),
        "SC": Decimal("17.00"),
        "RS": Decimal("17.00"),
        "BA": Decimal("19.00"),
        "PE": Decimal("18.00"),
        "CE": Decimal("18.00"),
        "GO": Decimal("17.00"),
        "DF": Decimal("18.00"),
        "MT": Decimal("17.00"),
        "MS": Decimal("17.00"),
        "PA": Decimal("17.00"),
        "AM": Decimal("18.00"),
        "RN": Decimal("18.00"),
        "PB": Decimal("18.00"),
        "AL": Decimal("18.00"),
        "SE": Decimal("18.00"),
        "RO": Decimal("17.50"),
        "AC": Decimal("17.00"),
        "AP": Decimal("18.00"),
        "RR": Decimal("17.00"),
        "PI": Decimal("18.00"),
        "MA": Decimal("18.00"),
        "TO": Decimal("18.00"),
        "DEFAULT": Decimal("18.00"),
    },
)

# =========================
# Utils
# =========================

def _parse_date_any(s):
    """Aceita 'dd/mm/yyyy' ou 'yyyy-mm-dd' e retorna date, ou None."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None

def _month_bounds(d: date):
    """Retorna (primeiro_do_mes, ultimo_do_mes) para a data d."""
    first = d.replace(day=1)
    if d.month == 12:
        next_first = date(d.year + 1, 1, 1)
    else:
        next_first = date(d.year, d.month + 1, 1)
    last = next_first - timedelta(days=1)
    return first, last

def _as_money(v):
    """
    Converte valores monetários aceitando pt-BR ('1.960,29') e en-US ('1960.29').
    Retorna None quando vazio/inválido.
    """
    if v is None or v == "":
        return None
    s = str(v).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        try:
            return Decimal(str(float(s))).quantize(Decimal("0.01"))
        except Exception:
            return None

def _as_decimal(v, q=4):
    """Converte valores (str/num) para Decimal com q casas. None quando inválido."""
    if v is None or v == "":
        return None
    try:
        return round(Decimal(str(v)), q)
    except (InvalidOperation, ValueError):
        return None

def _as_int(v):
    """Converte para inteiro de forma segura. None quando inválido."""
    if v is None or v == "":
        return None
    try:
        s = str(v).strip().replace(",", ".")
        d = Decimal(s)
        return int(d.to_integral_value(rounding=None))
    except (InvalidOperation, ValueError):
        try:
            return int(v)
        except Exception:
            return None

def _to_str_upper(v):
    """Normaliza para string maiúscula ou None."""
    if v is None:
        return None
    s = str(v).strip()
    return s.upper() if s else None

def _norm_code(s):
    """Remove pontuações e deixa maiúsculo para casar 'C35.001' com 'C35001'."""
    return re.sub(r"[^A-Za-z0-9]", "", (s or "")).upper() or None

def _code_variants(cod_norm: str):
    """
    Gera variações plausíveis do código normalizado para casar banco vs API.
    Ex.: 'K10009MO' -> ['K10009MO', 'K10009'].
    """
    if not cod_norm:
        return []
    variants = [cod_norm]
    sem_suf = re.sub(r"[A-Z]+$", "", cod_norm)
    if sem_suf and sem_suf != cod_norm:
        variants.append(sem_suf)
    sem_suf2 = re.sub(r"(\d{2,})[A-Z]+$", r"\1", cod_norm)
    if sem_suf2 and sem_suf2 not in variants:
        variants.append(sem_suf2)
    return variants

def _hash_unico(nfe, cliente_codigo, cliente, ocorrencia, item_codigo, item_valor_unitario, item_qtd, valor_frete):
    """Chave idempotente p/ FaturamentoRegistro."""
    occ_str = ocorrencia.strftime("%Y-%m-%d") if ocorrencia else ""
    base = (
        f"{nfe or ''}|{cliente_codigo or ''}|{cliente or ''}|{occ_str}|"
        f"{item_codigo or ''}|{item_valor_unitario or ''}|{item_qtd or ''}|{valor_frete or ''}"
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def _split_cliente(raw: str):
    """
    'C35 - CORDOBA'  -> ('C35', 'CORDOBA')
    'C35- CORDOBA'   -> ('C35', 'CORDOBA')
    'C35 CORDOBA'    -> (None, 'C35 CORDOBA')
    """
    if not raw:
        return (None, None)
    m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*-\s*(.+)$", str(raw).strip())
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    return (None, str(raw).strip())

def _flatten_vendas(lista):
    """
    Transforma cada venda (com 'itens') em linhas 1:1 por item, replicando campos do cabeçalho.
    Se a API trouxer 'cod_cliente', utiliza-o; caso contrário tenta extrair de 'cliente' ('COD - NOME').
    """
    saida = []
    for v in (lista or []):
        itens = v.get("itens") or []
        cli_cod_api = v.get("cod_cliente")
        cli_nome_api = v.get("cliente")
        cod, nome = _split_cliente(cli_nome_api)
        cliente_codigo_raw = (cod or cli_cod_api)
        cliente_nome = nome if nome else cli_nome_api

        base = {
            "nfe": v.get("nfe"),
            "ocorrencia": v.get("ocorrencia"),
            "cliente_codigo": cliente_codigo_raw,  # normaliza depois
            "cliente": cliente_nome,  # apenas nome
            "valor_frete": v.get("valor_frete"),
        }
        for it in itens:
            row = dict(base)
            row.update(
                {
                    "item_codigo": it.get("codigo"),
                    "item_quantidade": it.get("quantidade"),
                    "item_valor_unitario": it.get("valor_unitario"),
                    "item_ipi": it.get("ipi"),
                }
            )
            saida.append(row)
    return saida

def _extrair_lote(payload):
    """
    Normaliza payloads para lista.
    Suporta: lista direta; dict com 'registros', 'data', 'itens', 'notas', 'rows', 'results'
             dict com chaves numéricas '0','1',...
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for k in ("registros", "Registros", "data", "Data", "itens", "Itens", "notas", "Notas", "rows", "Rows", "results", "Results"):
            v = payload.get(k)
            if isinstance(v, list):
                return v

        numericas = [k for k in payload.keys() if str(k).isdigit()]
        numericas.sort(key=lambda s: int(s))
        lote = [payload[k] for k in numericas if isinstance(payload.get(k), dict)]
        if lote:
            return lote

    return []

def _get_cliente_uf(cli):
    """Retorna UF do cliente vinculado (usa apenas Cliente.uf)."""
    if not cli or not getattr(cli, "uf", None):
        return None
    return str(cli.uf).strip().upper()[:2]

# =========================
# Notas Fiscais – buscas por período (paginadas)
# =========================

def _fetch_nfs_periodo_paginado(client, data_inicio: str, data_fim: str, registros="200"):
    """
    Busca NFs do período com paginação.
    Parâmetros mínimos (iguais ao Power Query): dataInicio, dataFim, registros, pagina.
    Sem 'todos'. 'tipo' não é necessário.
    """
    try:
        di = _parse_date_any(data_inicio) or datetime.strptime(data_inicio, "%Y-%m-%d").date()
        df = _parse_date_any(data_fim) or datetime.strptime(data_fim, "%Y-%m-%d").date()
    except Exception:
        di = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        df = datetime.strptime(data_fim, "%Y-%m-%d").date()

    agregados = []
    pagina = 1
    total_paginas = None

    while True:
        params = {
            "dataInicio": di.strftime("%Y-%m-%d"),
            "dataFim": df.strftime("%Y-%m-%d"),
            "registros": str(registros),
            "pagina": str(pagina),
        }
        _dbg(f"GET NotasFiscais (período) {params['dataInicio']}→{params['dataFim']} pag={pagina} regs={registros}")
        try:
            payload = client.fetch_notas_fiscais(params=params)
        except Exception as e:
            _dbg(f"  ERRO período: {e}")
            break

        lote = _extrair_lote(payload) or []
        _dbg(f"  Lote={len(lote)}")
        agregados.extend(lote)

        # total_paginas (quando existir)
        tp = None
        if isinstance(payload, dict):
            tp = payload.get("total_paginas") or payload.get("TotalPaginas") or payload.get("totalPaginas")
        try:
            total_paginas = int(tp) if tp is not None else total_paginas
        except Exception:
            total_paginas = None

        # Regras de parada
        if total_paginas is not None:
            if pagina >= total_paginas:
                break
        else:
            if not lote or len(lote) < int(registros):
                break
        pagina += 1

    return agregados

def _fetch_nfs_periodo_com_fallback_mes(client, data_inicio: str, data_fim: str, registros="200"):
    """
    Primeiro tenta o intervalo informado. Se vier vazio, expande para as janelas mensais
    que cobrem (data_inicio..data_fim) — estratégia idêntica à do Power Query.
    """
    lote = _fetch_nfs_periodo_paginado(client, data_inicio, data_fim, registros=registros)
    if lote:
        return lote

    # Fallback: cobrir meses inteiros
    try:
        di = _parse_date_any(data_inicio) or datetime.strptime(data_inicio, "%Y-%m-%d").date()
        df = _parse_date_any(data_fim) or datetime.strptime(data_fim, "%Y-%m-%d").date()
    except Exception:
        di = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        df = datetime.strptime(data_fim, "%Y-%m-%d").date()

    di_first, _ = _month_bounds(di)
    _, df_last = _month_bounds(df)
    _dbg(f"Fallback mensal -> {di_first}..{df_last}")
    return _fetch_nfs_periodo_paginado(client, di_first.isoformat(), df_last.isoformat(), registros=registros)

# =========================
# Upsert de Duplicatas (NFs)
# =========================

def _upsert_duplicatas_de_lote_nf(lote_nf):
    """
    Insere/atualiza FaturamentoDuplicata a partir de um lote de NFs.
    Agora também tenta vincular o Cliente por NOME normalizado quando não houver código.
    """
    import unicodedata
    ins = upd = skip = 0

    def _alias(src, *keys):
        if isinstance(src, dict):
            for k in keys:
                v = src.get(k)
                if v not in (None, ""):
                    return v
        return None

    def _norm_empresa(s: str) -> str:
        if not s:
            return ""
        s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII")
        s = s.upper()
        # remove sufixos/siglas comuns e pontuação
        import re
        s = re.sub(r"[^A-Z0-9 ]+", " ", s)
        s = re.sub(r"\b(LTDA|S/?A|SA|EPP|MEI?|MICROEMPRESA|IND(USTRIA)?\.?|COM(ERCIO)?\.?|FAB(RICA)?|GRUPO|HOLDING|DA|DE|DO|DOS|DAS)\b", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # índice em memória: nome normalizado -> (id, fantasia, razao)
    name_index = {}
    for row in Cliente.objects.values("id", "nome_fantasia", "razao_social", "cod_bm"):
        for nm in (row["nome_fantasia"], row["razao_social"]):
            if nm:
                name_index[_norm_empresa(nm)] = (row["id"], row["nome_fantasia"] or "", row["razao_social"] or "")

    for nf in (lote_nf or []):
        numero_nf = str(nf.get("numero") or "").strip()
        if not numero_nf:
            continue

        duplics = nf.get("duplicatas") or []
        itens = nf.get("itens") or []

        dt_emissao_nf = _parse_date_any(_alias(nf, "emissao", "data", "data_emissao"))

        # Dados do cliente vindos da NF
        cli_nome_nf = _alias(nf, "cliente", "destinatario", "razao_social", "nome_cliente")
        cli_cod_nf  = _alias(nf, "cod_cliente", "codigo_cliente", "codigo_destinatario")

        # Resolve Cliente:
        cliente_obj = None

        # a) por código (quando existir)
        if cli_cod_nf:
            cliente_obj = (
                Cliente.objects.filter(cod_bm__isnull=False)
                .filter(cod_bm__iexact=str(cli_cod_nf).strip().upper())
                .only("id")
                .first()
            )

        # b) por nome normalizado (quando não houver código)
        if not cliente_obj and cli_nome_nf:
            key = _norm_empresa(cli_nome_nf)
            tupla = name_index.get(key)
            if tupla:
                cliente_obj = Cliente.objects.only("id").get(id=tupla[0])

        # --- CFOP, tributos etc. (mantém sua lógica) ---
        cfop_nf = _alias(nf, "cfop", "cfop_codigo")
        if not cfop_nf:
            for it in itens:
                cand = _alias(it, "cfop", "cfop_codigo")
                if cand:
                    cfop_nf = str(cand).strip()
                    break

        # IPI (R$) consolidado
        valor_ipi_nf = _as_money(_alias(nf, "valor_ipi", "valorIPI"))
        if valor_ipi_nf is None and itens:
            from decimal import Decimal
            total_ipi = Decimal("0.00")
            for it in itens:
                vi = (
                    _as_money(_alias(it, "valor_ipi", "valorIPI"))
                    or _as_money(_alias((it.get("ipi") or {}), "valor", "vIPI", "vipi"))
                )
                if vi is not None:
                    total_ipi += vi
            valor_ipi_nf = total_ipi if total_ipi != Decimal("0.00") else None

        # ICMS (R$) consolidado
        valor_icms_nf = _as_money(_alias(nf, "valor_icms", "valorICMS"))
        if valor_icms_nf is None and itens:
            from decimal import Decimal
            total_icms = Decimal("0.00")
            achou_icms = False
            for it in itens:
                vi = (
                    _as_money(_alias(it, "valor_icms", "valorICMS"))
                    or _as_money(_alias((it.get("icms") or {}), "valor", "vICMS", "vicms"))
                )
                if vi is not None:
                    total_icms += vi
                    achou_icms = True
            valor_icms_nf = total_icms if achou_icms else None

        # PIS (R$) consolidado
        pis_nf = _as_money(_alias(nf, "valor_pis", "valorPIS"))
        if pis_nf is None and itens:
            from decimal import Decimal
            total_pis = Decimal("0.00")
            for it in itens:
                vp = (
                    _as_money(_alias(it, "valor_pis", "valorPIS"))
                    or _as_money(_alias((it.get("pis") or {}), "valor", "vPIS", "vpis"))
                )
                if vp is not None:
                    total_pis += vp
            pis_nf = total_pis if total_pis != Decimal("0.00") else None

        # COFINS (R$) consolidado
        cofins_nf = _as_money(_alias(nf, "valor_cofins", "valorCOFINS"))
        if cofins_nf is None and itens:
            from decimal import Decimal
            total_cof = Decimal("0.00")
            for it in itens:
                vc = (
                    _as_money(_alias(it, "valor_cofins", "valorCOFINS"))
                    or _as_money(_alias((it.get("cofins") or {}), "valor", "vCOFINS", "vcofins"))
                )
                if vc is not None:
                    total_cof += vc
            cofins_nf = total_cof if total_cof != Decimal("0.00") else None

        for d in duplics:
            num_parc = d.get("numero")
            dt_venc  = _parse_date_any(d.get("data_vencimento"))
            val_dup  = _as_money(d.get("valor_duplicata"))
            if val_dup is None:
                continue

            chave = FaturamentoDuplicata._hash(numero_nf, num_parc, dt_venc, val_dup)

            cfop_nf_calc = nf.get("cfop") or d.get("cfop") or cfop_nf

            valor_pis_final    = _as_money(nf.get("valor_pis")    or d.get("valor_pis")    or pis_nf)
            valor_cofins_final = _as_money(nf.get("valor_cofins") or d.get("valor_cofins") or cofins_nf)
            valor_ipi_final    = _as_money(nf.get("valor_ipi")    or d.get("valor_ipi")    or valor_ipi_nf)
            valor_icms_final   = _as_money(nf.get("valor_icms")   or d.get("valor_icms")   or valor_icms_nf)

            allowed_fields = {
                f.name for f in FaturamentoDuplicata._meta.get_fields()
                if hasattr(f, "attname")
            }
            defaults_raw = {
                "nfe": numero_nf,
                "numero_parcela": num_parc,
                "data_vencimento": dt_venc,
                "valor_duplicata": val_dup,
                "cliente_codigo": _to_str_upper(cli_cod_nf),
                "cliente": cli_nome_nf,
                "cliente_vinculado": cliente_obj,   # ✅ agora com vinculação por nome quando necessário
                "ocorrencia": dt_emissao_nf,
                "natureza": nf.get("natureza") or d.get("natureza"),
                "cfop": cfop_nf_calc,
                "valor_pis": valor_pis_final,
                "valor_cofins": valor_cofins_final,
                "valor_ipi": valor_ipi_final,
                "valor_icms": valor_icms_final,
            }
            defaults = {k: v for k, v in defaults_raw.items() if k in allowed_fields}

            obj, created = FaturamentoDuplicata.objects.update_or_create(
                chave_unica=chave,
                defaults=defaults,
            )
            if created:
                ins += 1
            else:
                upd += 1

    return ins, upd, skip




# =========================
# Sincronização VENDAS (independente, usada no botão "Sync Vendas")
# =========================

def sincronizar_vendas(data_inicio: str, data_fim: str, pagina="1", registros="500", sobrescrever: bool = False):
    """
    GetVendas -> FaturamentoRegistro.
    Retorna (ins, upd, skip) e também o mapa vendas_por_nf para uso opcional.
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
        acumulado.extend(lote or [])

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
        nfe = (d.get("nfe") or None)
        ocorrencia = _parse_date_any(d.get("ocorrencia"))
        cliente_codigo = _to_str_upper(d.get("cliente_codigo"))
        cliente = d.get("cliente")
        valor_frete = _as_decimal(d.get("valor_frete"), q=2)

        codigo = _to_str_upper(d.get("item_codigo"))
        quantidade = _as_int(d.get("item_quantidade"))
        valor_unitario = _as_decimal(d.get("item_valor_unitario"), q=4)
        ipi = _as_decimal(d.get("item_ipi"), q=2)

        cliente_obj = None
        if cliente_codigo:
            cliente_obj = (
                Cliente.objects.filter(cod_bm__isnull=False)
                .filter(cod_bm__iexact=cliente_codigo)
                .first()
            )

        chave = _hash_unico(
            nfe, cliente_codigo, cliente, ocorrencia, codigo, valor_unitario, quantidade, valor_frete
        )

        if not sobrescrever:
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
                },
            )
            if created:
                ins += 1
            else:
                skip += 1
            continue

        obj = FaturamentoRegistro.objects.filter(chave_unica=chave).first()
        if obj:
            if getattr(obj, "congelado", False):
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

    # mapa auxiliar por NF (retornado apenas para quem quiser usar em outro lugar)
    vendas_por_nf = {}
    for d in linhas:
        n_raw = str(d.get("nfe") or "").strip()
        if not n_raw:
            continue
        somente_digitos = "".join(ch for ch in n_raw if ch.isdigit())
        n_norm = somente_digitos if somente_digitos else n_raw
        meta_cliente = {
            "cliente_codigo": _to_str_upper(d.get("cliente_codigo")),
            "cliente": d.get("cliente"),
            "ocorrencia": _parse_date_any(d.get("ocorrencia")),
        }
        vendas_por_nf[n_norm] = meta_cliente
        vendas_por_nf[n_raw] = meta_cliente

    return ins, upd, skip, vendas_por_nf

# =========================
# Sincronização NOTAS (Duplicatas + ICMS) — 100% por período (sem reconsulta por número)
# =========================

def _coletar_icms_map(lote_nf):
    """
    A partir do lote de NFs, monta:
      - icms_map: (numero_str, COD_NORMALIZADO) -> Decimal(aliquota)
      - icms_nf_default: numero_str -> Decimal(aliquota) se todos os itens válidos forem iguais
    """
    icms_map = {}
    icms_nf_default = {}

    for nf in (lote_nf or []):
        numero_nf = str(nf.get("numero") or "").strip()
        itens = nf.get("itens") or []
        aliqs_validas = []

        for it in itens:
            cod = _norm_code(it.get("cod_produto"))
            if not numero_nf or not cod:
                continue
            perc = it.get("perc_icms")
            if perc is None and isinstance(it.get("icms"), dict):
                perc = it["icms"].get("aliquota")
            dec = _as_decimal(perc, q=2)
            icms_map[(numero_nf, cod)] = dec
            if dec is not None:
                aliqs_validas.append(dec)

        if aliqs_validas:
            uniq = {str(x) for x in aliqs_validas}
            if len(uniq) == 1:
                icms_nf_default[numero_nf] = aliqs_validas[0]

    return icms_map, icms_nf_default

def _aplicar_icms(icms_map, icms_nf_default):
    """
    Aplica ICMS em FaturamentoRegistro (tipo Venda), com fallback por UF.
    Retorna (hit_atualizado, hit_sem_mudanca, estatísticas auxiliares).
    """
    hit_atualizado = hit_sem_mudanca = 0
    miss_frozen = miss_tipo = miss_sem_nf = miss_sem_item = miss_sem_map = 0
    hit_item = hit_nf_default = hit_uf_default = 0

    if not icms_map and not icms_nf_default:
        _dbg("Sem ICMS coletado do lote — nada a aplicar.")
        return 0, 0, {
            "frozen": 0, "tipo": 0, "sem_nf": 0, "sem_item": 0, "sem_map": 0,
            "hit_item": 0, "hit_nf_default": 0, "hit_uf_default": 0
        }

    candidatos_qs = (
        FaturamentoRegistro.objects.select_related("cliente_vinculado")
        .filter(ocorrencia__isnull=False)
        .exclude(nfe__isnull=True)
        .exclude(nfe__exact="")
    )
    candidatos = list(candidatos_qs)
    _dbg(f"Candidatos p/ aplicar ICMS: {len(candidatos)}")

    for r in candidatos:
        if (getattr(r, "tipo", None) or "Venda") != "Venda":
            miss_tipo += 1
            continue
        if getattr(r, "congelado", False):
            miss_frozen += 1
            continue

        nfe_raw = r.nfe
        if not nfe_raw:
            miss_sem_nf += 1
            continue

        cod_norm = _norm_code(r.item_codigo)
        if not cod_norm:
            miss_sem_item += 1
            continue

        nfe_keys = [str(nfe_raw).strip()]
        try:
            nfe_keys.append(str(int(nfe_keys[0])))
        except Exception:
            pass

        novo_icms = None

        # 1) por ITEM
        for nfk in nfe_keys:
            for cod_try in _code_variants(cod_norm):
                novo_icms = icms_map.get((nfk, cod_try))
                if novo_icms is not None:
                    hit_item += 1
                    _dbg("HIT item", {"nf": nfk, "item": r.item_codigo, "cod_try": cod_try, "aliq": str(novo_icms)})
                    break
            if novo_icms is not None:
                break

        # 2) default por NF
        if novo_icms is None:
            for nfk in nfe_keys:
                nf_def = icms_nf_default.get(nfk)
                if nf_def is not None:
                    novo_icms = nf_def
                    hit_nf_default += 1
                    _dbg("HIT nf_default", {"nf": nfk, "aliq": str(novo_icms)})
                    break

        # 3) fallback por UF do cliente
        if novo_icms is None:
            cli = getattr(r, "cliente_vinculado", None)
            uf = _get_cliente_uf(cli)
            if uf:
                novo_icms = ICMS_DEFAULT_BY_UF.get(uf, ICMS_DEFAULT_BY_UF.get("DEFAULT"))
                hit_uf_default += 1
                _dbg("HIT uf_default", {"nf": nfe_keys[0], "item": r.item_codigo, "uf": uf, "aliq": str(novo_icms)})
            else:
                _dbg("MISS uf_default_sem_uf", {"nf": nfe_keys[0], "item": r.item_codigo})

        if novo_icms is None:
            miss_sem_map += 1
            continue

        atual = None if r.perc_icms is None else Decimal(str(r.perc_icms)).quantize(Decimal("0.01"))
        novo = Decimal(str(novo_icms)).quantize(Decimal("0.01"))

        if atual != novo:
            r.perc_icms = novo
            r.save(update_fields=["perc_icms"])
            hit_atualizado += 1
        else:
            hit_sem_mudanca += 1

    _dbg(
        "APLICAÇÃO -> "
        f"atualizados={hit_atualizado} | sem_mudanca={hit_sem_mudanca} | "
        f"por_item={hit_item} | por_nf_default={hit_nf_default} | por_uf_default={hit_uf_default} | "
        f"frozen={miss_frozen} | tipo!=Venda={miss_tipo} | sem_nf={miss_sem_nf} | "
        f"sem_item={miss_sem_item} | sem_map={miss_sem_map}"
    )

    return hit_atualizado, hit_sem_mudanca, {
        "frozen": miss_frozen,
        "tipo": miss_tipo,
        "sem_nf": miss_sem_nf,
        "sem_item": miss_sem_item,
        "sem_map": miss_sem_map,
        "hit_item": hit_item,
        "hit_nf_default": hit_nf_default,
        "hit_uf_default": hit_uf_default,
    }

def sincronizar_notas_fiscais(data_inicio: str, data_fim: str, registros="500"):
    """
    GetNotasFiscais por período (independente de GetVendas):
      - upsert de FaturamentoDuplicata (todas as naturezas) a partir do lote do período
      - coleta perc_icms por item no próprio lote e aplica em FaturamentoRegistro
    Retorna (dup_ins, icms_atualizados, dup_skip).
    """
    client = BrasmolClient()

    # 1) Coletar NFs do período (com fallback para janela mensal, igual PQ)
    lote_nf_full = _fetch_nfs_periodo_com_fallback_mes(client, data_inicio, data_fim, registros="200") or []
    _dbg(f"Coleta período total: {len(lote_nf_full)} NFs")

    # 2) Upsert duplicatas direto do lote
    dup_ins, dup_upd, dup_skip = _upsert_duplicatas_de_lote_nf(lote_nf_full)

    # 3) Coletar ICMS a partir do próprio lote e aplicar
    icms_map, icms_nf_default = _coletar_icms_map(lote_nf_full)
    _dbg(f"ICMS map chaves={len(icms_map)} | NF defaults={len(icms_nf_default)}")

    hit_upd, _hit_unch, _stats = _aplicar_icms(icms_map, icms_nf_default)

    return (dup_ins + dup_upd), hit_upd, dup_skip

# =========================
# Orquestradores expostos às views
# =========================

@transaction.atomic
def sincronizar_faturamento(data_inicio: str, data_fim: str, pagina: str = "1", registros: str = "500", sobrescrever: bool = False):
    """
    Sincroniza apenas VENDAS (GetVendas) -> FaturamentoRegistro.
    """
    ins_v, upd_v, skip_v, _ = sincronizar_vendas(
        data_inicio, data_fim, pagina=pagina, registros=registros, sobrescrever=sobrescrever
    )
    return ins_v, upd_v, skip_v

@transaction.atomic
def sincronizar_faturamento_notas(data_inicio: str, data_fim: str, registros: str = "500"):
    """
    NOTAS 100% independentes de GetVendas.
    - Busca por período (com fallback mensal, sem 'todos')
    - Upsert de duplicatas e atualização de ICMS a partir do próprio lote
    """
    print(f"[SYNC-NOTAS:WRAPPER] período={data_inicio} -> {data_fim} | regs={registros}")
    dup_ins, icms_upd, dup_skip = sincronizar_notas_fiscais(
        data_inicio=data_inicio,
        data_fim=data_fim,
        registros=registros,
    )
    print(f"[SYNC-NOTAS:RESULT] duplicatas_ins={dup_ins} | icms_upd={icms_upd} | duplicatas_skip={dup_skip}")
    return dup_ins, icms_upd, dup_skip