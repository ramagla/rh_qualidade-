// init_eventos_f045.js — Certificado espelhando a lógica dos rolos, com logs completos
(function () {
  console.log("[F045] init_eventos_f045.js carregado");

  const FATOR_CONVERSAO = 0.10197; // MPa -> Kgf/mm²
  const LOG = (...a) => { try { console.log("[F045/Cert]", ...a); } catch(_){} };

  // ---------- Utils ----------
  function parseNum(v) {
    if (v === undefined || v === null) return NaN;
    return parseFloat(String(v).replace(",", ".").replace(/[^\d.]/g, ""));
  }
  function emMpa() {
    const sw = document.getElementById("switchMpa");
    const flag = sw?.checked === true;
    LOG("Unidade em MPa?", flag);
    return flag;
  }
  function getLaudoEl() {
    const el = document.getElementById("laudo_certificado");
    if (!el) LOG("❗ #laudo_certificado não encontrado no DOM.");
    else LOG("laudo_certificado encontrado:", el.tagName, el);
    return el;
  }
  function setLaudo(aprovado, neutro=false) {
    const el = getLaudoEl();
    if (!el) return;
    const tag = el.tagName?.toLowerCase();
    const texto = neutro ? "—" : (aprovado ? "Aprovado" : "Reprovado");
    const classeBase = "form-control fw-bold text-center ";
    const classe = neutro ? (classeBase + "text-muted") : (classeBase + (aprovado ? "text-success" : "text-danger"));

    if (tag === "input" || tag === "textarea") {
      el.value = texto;
      el.className = classe;
    } else {
      el.textContent = texto;
      el.className = classe;
    }
  }

  // ---------- Limites da NORMA (mesma fonte dos rolos) ----------
  function getRoloBaseId() {
    const anyTracao = document.querySelector('input[id^="tracao_"]');
    if (anyTracao) {
      const id = anyTracao.id.split("_")[1];
      LOG("Rolo base por input tracao_:", id);
      return id;
    }
    const rminHidden = document.querySelector('input[id^="rmin_valor_"]');
    if (rminHidden) {
      const id = rminHidden.id.replace("rmin_valor_", "");
      LOG("Rolo base por hidden rmin_valor_:", id);
      return id;
    }
    LOG("❗ Não foi possível determinar rolo base.");
    return null;
  }

  function getLimitesDoRolo(roloId) {
    const rMin = parseNum(document.getElementById(`rmin_valor_${roloId}`)?.value);
    const rMax = parseNum(document.getElementById(`rmax_valor_${roloId}`)?.value);
    const durezaNorma = parseNum(document.getElementById(`dureza_${roloId}`)?.dataset?.durezaNorma);
    LOG("Limites lidos do rolo base:", { roloId, rMin, rMax, durezaNorma });
    return { rMin, rMax, durezaNorma };
  }

  // ---------- Validação do Certificado (espelha a dos rolos) ----------
  function validarCertificadoComoRolo() {
    const roloId = getRoloBaseId();
    const inputTracao = document.getElementById("id_resistencia_tracao");
    const inputDureza = document.getElementById("id_dureza_certificado");

    LOG("Validando Certificado…");
    if (!roloId) { LOG("Abortado: rolo base ausente."); return; }
    if (!inputTracao && !inputDureza) { LOG("Abortado: campos do certificado ausentes."); return; }

    const { rMin, rMax, durezaNorma } = getLimitesDoRolo(roloId);

    let tracaoCert = parseNum(inputTracao?.value);
    const durezaCert = parseNum(inputDureza?.value);
    const ambosVazios = isNaN(tracaoCert) && isNaN(durezaCert);

    // conversão da tração para base Kgf/mm² (igual aos rolos)
    if (!isNaN(tracaoCert) && emMpa()) {
      const antes = tracaoCert;
      tracaoCert = tracaoCert / FATOR_CONVERSAO;
      LOG(`Conversão MPa→Kgf/mm²: ${antes} → ${tracaoCert.toFixed(2)}`);
    }

    LOG("Dados p/ decisão:", { rMin, rMax, durezaNorma, tracaoCert, durezaCert });

    let tracaoOk = true;
    if (!isNaN(tracaoCert) && !isNaN(rMin) && !isNaN(rMax)) {
      tracaoOk = tracaoCert >= rMin && tracaoCert <= rMax;
    }

    let durezaOk = true;
    if (!isNaN(durezaNorma)) {
      // REPROVA se dureza do certificado excede o limite da norma
      durezaOk = !isNaN(durezaCert) && durezaCert <= durezaNorma;
    }

    const aprovado = tracaoOk && durezaOk;
    LOG(`Resultado: Tração OK? ${tracaoOk} | Dureza OK? ${durezaOk} | Laudo: ${aprovado ? "APROVADO" : "REPROVADO"}`);

    // feedback visual nos inputs
    if (inputTracao) {
      inputTracao.classList.toggle("is-valid", tracaoOk && !ambosVazios);
      inputTracao.classList.toggle("is-invalid", !tracaoOk && !isNaN(tracaoCert));
    }
    if (inputDureza) {
      inputDureza.classList.toggle("is-valid", durezaOk && !ambosVazios);
      inputDureza.classList.toggle("is-invalid", !durezaOk && !isNaN(durezaCert));
    }

    // laudo visual
    if (ambosVazios) setLaudo(true, /*neutro*/ true);
    else setLaudo(aprovado, /*neutro*/ false);

    // integra status geral
    if (typeof atualizarStatusGeral === "function") {
      LOG("Chamando atualizarStatusGeral()");
      atualizarStatusGeral();
    } else {
      LOG("⚠️ função atualizarStatusGeral() não encontrada.");
    }
  }

  // ---------- Binds ----------
  function bindCertificado() {
    const inputTracao = document.getElementById("id_resistencia_tracao");
    const inputDureza = document.getElementById("id_dureza_certificado");
    const switchMpa = document.getElementById("switchMpa");

    LOG("Registrando eventos do certificado:", {
      temTracao: !!inputTracao, temDureza: !!inputDureza, temSwitch: !!switchMpa
    });

    ["input", "change", "keyup"].forEach(evt => {
      if (inputTracao) inputTracao.addEventListener(evt, validarCertificadoComoRolo);
      if (inputDureza) inputDureza.addEventListener(evt, validarCertificadoComoRolo);
    });
    if (switchMpa) switchMpa.addEventListener("change", validarCertificadoComoRolo);

    // ao abrir o acordeão
    document.getElementById("collapseOutrasCaracteristicas")
      ?.addEventListener("shown.bs.collapse", validarCertificadoComoRolo);

    validarCertificadoComoRolo(); // primeira avaliação
  }

  function bindRolos() {
    document
      .querySelectorAll('input[id^="bitola_"], input[id^="tracao_"], input[id^="dureza_"]')
      .forEach((input) => {
        const id = input.id.split("_")[1];
        ["input", "change", "keyup"].forEach(evt =>
          input.addEventListener(evt, () => {
            console.log("🧪 Validando Rolo (evento)", id);
            if (typeof validarBitolaETracao === "function") validarBitolaETracao(id);
          })
        );
      });

    document.querySelectorAll('select[name^="rolos-"]').forEach((select) => {
      const match = select.name.match(/^rolos-(\d+)-/);
      if (match) {
        const index = match[1];
        select.addEventListener("change", () => {
          const roloId = document.querySelector(`input[name="rolos-${index}-id"]`)?.value;
          if (roloId && typeof validarBitolaETracao === "function") validarBitolaETracao(roloId);
        });
      }
    });
  }

  // Observa DOM dinâmico (formsets/acordeões) e revalida
  function observar() {
    let t = null;
    new MutationObserver(() => {
      clearTimeout(t);
      t = setTimeout(() => {
        LOG("MutationObserver → rebind + revalidação do certificado");
        bindCertificado();
        validarCertificadoComoRolo();
      }, 80);
    }).observe(document.body, { childList: true, subtree: true });
  }

  // expõe função p/ outros scripts (ex.: toggle_unidade_tracao) e para oninput no HTML
  window.__f045_validarCertificado = validarCertificadoComoRolo;
  window.validarCertificadoComoRolo = validarCertificadoComoRolo; // ✅ torna global para compatibilidade

  // inicializa
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      console.log("[F045] DOMContentLoaded");
      bindRolos();
      bindCertificado();
      observar();
    });
  } else {
    console.log("[F045] DOM já pronto");
    bindRolos();
    bindCertificado();
    observar();
  }
})();
