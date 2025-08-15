import hashlib
from decimal import Decimal, InvalidOperation
from django.db import transaction
from comercial.api_client import BrasmolClient
from comercial.models.faturamento import FaturamentoRegistro
from comercial.models.clientes import Cliente
import re
from datetime import datetime, timedelta


from django.conf import settings

# Tabela de fallback por UF — ideal é configurar no settings:
ICMS_DEFAULT_BY_UF = getattr(settings, "ICMS_DEFAULT_BY_UF", {
    # personalize conforme sua realidade!
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
    # fallback geral, caso a UF não exista nesta tabela:
    "DEFAULT": Decimal("18.00"),
})

def _get_cliente_uf(cli):
    """
    Retorna a UF (duas letras) do cliente vinculado.
    Compatível com seu modelo atual, que possui apenas o campo `uf`.
    """
    if not cli or not getattr(cli, "uf", None):
        return None
    return str(cli.uf).strip().upper()[:2]



DEBUG_ICMS = True  # deixe True para logar; mude para False para silenciar
def _dbg(*args):
    if DEBUG_ICMS:
        print("[SYNC-ICMS]", *args)

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

def _code_variants(cod_norm: str):
    """
    Gera variações plausíveis do código normalizado para casar banco vs API.
    Ex.: 'K10009MO' -> ['K10009MO', 'K10009']  (remove sufixo alfabético)
         'Z01030'   -> ['Z01030']             (sem mudanças)
    """
    if not cod_norm:
        return []
    variants = [cod_norm]

    # 1) remover sufixo estritamente alfabético no final (ex.: ...MO)
    sem_suf = re.sub(r"[A-Z]+$", "", cod_norm)
    if sem_suf and sem_suf != cod_norm:
        variants.append(sem_suf)

    # 2) (opcional) remover qualquer sufixo após 2 últimos dígitos contínuos
    #    Útil se houver mais de um sufixo (ex.: K10009MOX)
    sem_suf2 = re.sub(r"(\d{2,})[A-Z]+$", r"\1", cod_norm)
    if sem_suf2 and sem_suf2 not in variants:
        variants.append(sem_suf2)

    return variants

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
    occ_str = ocorrencia.strftime("%Y-%m-%d") if ocorrencia else ""
    base = (
        f"{nfe or ''}|{cliente_codigo or ''}|{cliente or ''}|{occ_str}|"
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
    _dbg(f"Iter NF: período {ini} → {fim}, step={step.days}d")

    while cursor <= fim:
        sub_ini = cursor
        sub_fim = min(cursor + step, fim)
        cursor = sub_fim + timedelta(days=1)
        _dbg(f"Subperíodo: {sub_ini} → {sub_fim}")

        # retries com tamanhos de página menores
        for reg_try in [int(registros), 200, 100, 50]:
            pagina_atual = 1
            falhou = False
            _dbg(f"  Tamanho página: {reg_try}")
            while True:
                params = {
                    "dataInicio": sub_ini.strftime("%Y-%m-%d"),
                    "dataFim": sub_fim.strftime("%Y-%m-%d"),
                    "tipo": "json",
                    "pagina": str(pagina_atual),
                    "registros": str(reg_try),
                }
                try:
                    _dbg(f"    GET NotasFiscais pag={pagina_atual} regs={reg_try}")
                    payload = client.fetch_notas_fiscais(params)
                except Exception as e:
                    _dbg(f"    ERRO request: {e}")
                    falhou = True
                    break

                lote = _extrair_lote(payload)
                tam = len(lote) if isinstance(lote, list) else 0
                _dbg(f"    Lote tamanho={tam}")
                if lote:
                    yield lote

                # Heurística de parada: vazio ou menor que page size
                if not lote or tam < reg_try:
                    break
                pagina_atual += 1

            if not falhou:
                _dbg("  OK subperíodo concluído.")
                break
            else:
                _dbg("  Falhou; tentando tamanho de página menor...")




@transaction.atomic
def sincronizar_faturamento(data_inicio: str, data_fim: str, pagina="1", registros="500", sobrescrever: bool = False):
    """
    Busca na API GetVendas e insere/atualiza em FaturamentoRegistro.
    """
    _dbg(f"=== INICIO SYNC FATURAMENTO === {data_inicio} → {data_fim} | sobrescrever={sobrescrever} | regs={registros}")

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
        ocorrencia = _parse_date_any(d.get("ocorrencia"))  

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
        # ---- Segunda fase: buscar Notas Fiscais (por número) e atualizar perc_icms por item ----
    # 1) Colete NFs + datas (para fallback por data se 'nota' falhar)
    nfs_alvo = set()
    nf_occ_map = {}  # nf_str -> lista[date]

    for d in linhas:
        n_raw = d.get("nfe")
        if not n_raw:
            continue
        n = str(n_raw).strip()
        if not n or n.lower() == "vale":
            continue

        nfs_alvo.add(n)
        try:
            nfs_alvo.add(str(int(n)))
        except Exception:
            pass

        dt = _parse_date_any(d.get("ocorrencia"))
        if dt:
            nf_occ_map.setdefault(n, []).append(dt)

    _dbg(f"Buscar NF por numero (API param 'nota'): total_unicos={len(nfs_alvo)} amostra={list(sorted(nfs_alvo))[:10]}")


    # 2) Busca por NF específica usando o parâmetro 'nota' (datas não são necessárias)
    from time import sleep

    def _fetch_nf_por_nota(client, nf_num: str, page_size: int = 200):
        """
        Tenta pela 'nota' (200→100→50). Se falhar ou vier vazio e tivermos data de ocorrência,
        faz fallback por data (±2 dias). Retorna (lote_nfs, meta_debug).
        """
        meta = {"nf": nf_num, "tentativas": [], "fallback_data": None, "status": "ok"}

        # 1) por nota
        for ps in (page_size, 100, 50):
            params = {"nota": str(nf_num), "tipo": "json", "pagina": "1", "registros": str(ps)}
            meta["tentativas"].append({"modo": "nota", "params": dict(params)})
            try:
                _dbg(f"  GET NotasFiscais (nota) nf={nf_num} regs={ps}")
                payload = client.fetch_notas_fiscais(params=params)
                lote = _extrair_lote(payload)
                _dbg(f"    resposta (nota) nf={nf_num} itens={len(lote) if isinstance(lote, list) else 0}")
                if lote:
                    return lote, meta
                break  # vazio → tenta fallback por data
            except Exception as e:
                _dbg(f"    ERRO (nota) nf={nf_num}: {e}")
                sleep(0.15)
                continue

        # 2) fallback por data (quando possível)
        if nf_num in nf_occ_map:
            dts = nf_occ_map[nf_num]
            j_ini = (min(dts) - timedelta(days=2)).strftime("%Y-%m-%d")
            j_fim = (max(dts) + timedelta(days=2)).strftime("%Y-%m-%d")
            meta["fallback_data"] = {"dataInicio": j_ini, "dataFim": j_fim}

            for ps in (200, 100, 50):
                params = {"dataInicio": j_ini, "dataFim": j_fim, "tipo": "json", "pagina": "1", "registros": str(ps)}
                meta["tentativas"].append({"modo": "data", "params": dict(params)})
                try:
                    _dbg(f"  GET NotasFiscais (data) nf={nf_num} {j_ini}→{j_fim} regs={ps}")
                    payload = client.fetch_notas_fiscais(params=params)
                    lote = _extrair_lote(payload)
                    lote_nf = [x for x in (lote or []) if str(x.get("numero") or "").strip() == str(nf_num)]
                    _dbg(f"    resposta (data) nf={nf_num} lote={len(lote or [])} lote_nf={len(lote_nf)}")
                    if lote_nf:
                        return lote_nf, meta
                except Exception as e:
                    _dbg(f"    ERRO (data) nf={nf_num}: {e}")
                    sleep(0.15)
                    continue

        meta["status"] = "fail"
        return [], meta

    # 2) Busca com retries + fallback e construção do mapa
    icms_map = {}           # (numero_str, COD_NORMALIZADO) -> Decimal(aliquota)
    icms_nf_default = {}    # numero_str -> Decimal(aliquota) se todos os itens válidos forem iguais
    ok_busca = err_busca = vazias = 0
    debug_falhas = []

    for nf_num in sorted(nfs_alvo):
        lote, meta = _fetch_nf_por_nota(client, nf_num, page_size=200)
        if meta["status"] == "fail":
            err_busca += 1
            debug_falhas.append(meta)
            continue
        if not lote:
            vazias += 1
            debug_falhas.append(meta)
            continue

        ok_busca += 1
        for nf in lote:
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

            # se todos os itens válidos desta NF têm a MESMA alíquota, guardamos um default por NF
            if aliqs_validas:
                uniq = {str(x) for x in aliqs_validas}
                if len(uniq) == 1:
                    icms_nf_default[numero_nf] = aliqs_validas[0]

        sleep(0.15)

    _dbg(f"Coleta por 'nota': ok={ok_busca} vazias={vazias} erros={err_busca} | icms_map_chaves={len(icms_map)}")
    if debug_falhas:
        _dbg("Falhas por NF (amostra):", debug_falhas[:5])


    # 3) Aplicar no banco (com amostras de HIT/MISS)
    # (INICIALIZA OS CONTADORES FORA DO if para evitar UnboundLocalError)
    # 3) Aplicar no banco (com amostras de HIT/MISS)
    # (INICIALIZA OS CONTADORES FORA DO if para evitar UnboundLocalError)
    hit_atualizado = hit_sem_mudanca = 0
    miss_frozen = miss_tipo = miss_sem_nf = miss_sem_item = miss_sem_map = 0
    hit_item = hit_nf_default = hit_uf_default = 0
    amostra_hit, amostra_miss = [], []

    if icms_map:
        from decimal import Decimal

        # Importante: NÃO usar .only(...) junto com select_related da FK que iremos acessar (cliente_vinculado.uf)
        candidatos_qs = (
            FaturamentoRegistro.objects
            .select_related("cliente_vinculado")
            .filter(ocorrencia__isnull=False)   # ✅ apenas isnull=False
            .exclude(nfe__isnull=True).exclude(nfe__exact="")
        )

        candidatos = list(candidatos_qs)
        _dbg(f"Candidatos p/ aplicar ICMS: {len(candidatos)}")

        for r in candidatos:
            # só vendas; ignore congelados
            if (getattr(r, "tipo", None) or "Venda") != "Venda":
                miss_tipo += 1
                continue
            if getattr(r, "congelado", False):
                miss_frozen += 1
                continue

            # NF e item
            nfe_raw = r.nfe
            if not nfe_raw:
                miss_sem_nf += 1
                continue

            cod_norm = _norm_code(r.item_codigo)
            if not cod_norm:
                miss_sem_item += 1
                continue

            # tente tanto "21253" quanto 21253→"21253"
            nfe_keys = [str(nfe_raw).strip()]
            try:
                nfe_keys.append(str(int(nfe_keys[0])))
            except Exception:
                pass

            novo_icms = None

            # 1) por ITEM (tenta variações do código: remove sufixos tipo "-MO", "*", etc.)
            for nfk in nfe_keys:
                for cod_try in _code_variants(cod_norm):
                    novo_icms = icms_map.get((nfk, cod_try))
                    if novo_icms is not None:
                        hit_item += 1
                        if DEBUG_ICMS:
                            _dbg("HIT item", {"nf": nfk, "item": r.item_codigo, "cod_try": cod_try, "aliq": str(novo_icms)})
                        break
                if novo_icms is not None:
                    break

            # 2) fallback: DEFAULT por NF (se todos os itens válidos daquela NF têm a mesma alíquota)
            if novo_icms is None and 'icms_nf_default' in locals():
                for nfk in nfe_keys:
                    nf_def = icms_nf_default.get(nfk)
                    if nf_def is not None:
                        novo_icms = nf_def
                        hit_nf_default += 1
                        if DEBUG_ICMS:
                            _dbg("HIT nf_default", {"nf": nfk, "aliq": str(novo_icms)})
                        break

            # 3) fallback: DEFAULT por UF do cliente vinculado (usa apenas Cliente.uf)
            if novo_icms is None:
                cli = getattr(r, "cliente_vinculado", None)
                uf = _get_cliente_uf(cli)  # agora olha somente para `cli.uf`
                if uf:
                    novo_icms = ICMS_DEFAULT_BY_UF.get(uf, ICMS_DEFAULT_BY_UF.get("DEFAULT"))
                    hit_uf_default += 1
                    if DEBUG_ICMS:
                        _dbg("HIT uf_default", {"nf": nfe_keys[0], "item": r.item_codigo, "uf": uf, "aliq": str(novo_icms)})
                else:
                    if DEBUG_ICMS:
                        _dbg("MISS uf_default_sem_uf", {"nf": nfe_keys[0], "item": r.item_codigo})

            # se mesmo assim não achou → contabiliza miss para análise
            if novo_icms is None:
                miss_sem_map += 1
                if len(amostra_miss) < 12:
                    amostra_miss.append({
                        "nfe_keys": nfe_keys,
                        "item": r.item_codigo,
                        "cod_norm": cod_norm,
                        "tries": _code_variants(cod_norm),
                    })
                continue

            # aplica se mudou
            atual = None if r.perc_icms is None else Decimal(str(r.perc_icms)).quantize(Decimal("0.01"))
            novo  = Decimal(str(novo_icms)).quantize(Decimal("0.01"))

            if atual != novo:
                r.perc_icms = novo
                r.save(update_fields=["perc_icms"])
                hit_atualizado += 1
                if len(amostra_hit) < 12:
                    amostra_hit.append({"nfe": nfe_keys[0], "item": r.item_codigo, "to": str(novo)})
            else:
                hit_sem_mudanca += 1

        _dbg(
            "APLICAÇÃO -> "
            f"atualizados={hit_atualizado} | sem_mudanca={hit_sem_mudanca} | "
            f"por_item={hit_item} | por_nf_default={hit_nf_default} | por_uf_default={hit_uf_default} | "
            f"frozen={miss_frozen} | tipo!=Venda={miss_tipo} | sem_nf={miss_sem_nf} | "
            f"sem_item={miss_sem_item} | sem_map={miss_sem_map}"
        )

        # reflete no resumo final
        upd += hit_atualizado


    _dbg(f"=== FIM SYNC FATURAMENTO === inseridos={ins} | atualizados={upd} | pulados={skip}")

    return ins, upd, skip

