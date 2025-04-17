function validarBitolaETracao(roloId) {
  console.clear();
  console.log(`🧪 Validando Rolo ID: ${roloId}`);

  const FATOR_CONVERSAO = 0.10197; // Fator para MPa ⇄ Kgf/mm²

  const tracaoInput = document.getElementById(`tracao_${roloId}`);
  const durezaInput = document.getElementById(`dureza_${roloId}`);
  const laudoCell = document.getElementById(`laudo_${roloId}`);
  const emMpa = document.getElementById("switchMpa").checked;

  const espInput = document.getElementById(`bitola_espessura_${roloId}`);
  const largInput = document.getElementById(`bitola_largura_${roloId}`);

  const bitolaNominal = parseFloat((document.getElementById(`bitola_nominal_${roloId}`)?.value || "0").replace(",", ".")) || 0;
  const larguraNominal = parseFloat((document.getElementById(`largura_nominal_${roloId}`)?.value || "0").replace(",", ".")) || 0;
  const toleranciaEsp = parseFloat((document.getElementById(`tolerancia_espessura_${roloId}`)?.value || "0").replace(",", ".")) || 0;
  const toleranciaLar = parseFloat((document.getElementById(`tolerancia_largura_${roloId}`)?.value || "0").replace(",", ".")) || 0;

  const rMin = parseFloat((document.getElementById(`rmin_valor_${roloId}`)?.value || "0").replace(",", ".")) || 0;
  const rMax = parseFloat((document.getElementById(`rmax_valor_${roloId}`)?.value || "0").replace(",", ".")) || 0;

  const rawDurezaNorma = durezaInput.dataset.durezaNorma;
  const durezaNormaParsed = rawDurezaNorma && rawDurezaNorma !== "—" ? parseFloat(rawDurezaNorma.replace(",", ".")) : null;

  const espessura = espInput ? parseFloat((espInput.value || "").replace(",", ".")) : null;
  const largura = largInput ? parseFloat((largInput.value || "").replace(",", ".")) : null;
  const tracao = tracaoInput ? parseFloat((tracaoInput.value || "").replace(",", ".")) : null;
  const dureza = durezaInput ? parseFloat((durezaInput.value || "").replace(",", ".")) : null;

  console.log("📋 Dados lidos:");
  console.table({
    bitolaNominal, larguraNominal, toleranciaEsp, toleranciaLar,
    espessura, largura, tracao, dureza,
    rMin, rMax, durezaNormaParsed
  });

  // Ajusta limites de tração se for MPa
  let rMinConvertido = rMin;
  let rMaxConvertido = rMax;
  if (emMpa) {
    rMinConvertido = rMin / FATOR_CONVERSAO;
    rMaxConvertido = rMax / FATOR_CONVERSAO;
    console.log(`🔄 Limites convertidos para MPa: Rmin=${rMinConvertido.toFixed(2)}, Rmax=${rMaxConvertido.toFixed(2)}`);
  }

  // Validação da Espessura
  let espOk = true;
  if (espessura !== null && !isNaN(espessura)) {
    const limiteInf = bitolaNominal - toleranciaEsp;
    const limiteSup = bitolaNominal + toleranciaEsp;
    espOk = espessura >= limiteInf && espessura <= limiteSup;
    console.log(`📏 Espessura: ${espessura} (entre ${limiteInf} e ${limiteSup}) ✅? ${espOk}`);
  }

  // Validação da Largura (se existir largura nominal)
  let largOk = true;
  if (larguraNominal !== 0 && largura !== null && !isNaN(largura)) {
    const limiteInf = larguraNominal - toleranciaLar;
    const limiteSup = larguraNominal + toleranciaLar;
    largOk = largura >= limiteInf && largura <= limiteSup;
    console.log(`📏 Largura: ${largura} (entre ${limiteInf} e ${limiteSup}) ✅? ${largOk}`);
  }

  // Validação da Tração
  let tracaoOk = true;
  if (tracao !== null && !isNaN(tracao)) {
    const valorValidar = emMpa ? tracao / FATOR_CONVERSAO : tracao;
    tracaoOk = valorValidar >= rMin && valorValidar <= rMax;
    console.log(`🔧 Tração validada: ${valorValidar.toFixed(2)} (entre ${rMin} e ${rMax}) ✅? ${tracaoOk}`);
  }

  // Validação da Dureza
  let durezaOk = true;
  if (durezaNormaParsed !== null) {
    durezaOk = dureza !== null && !isNaN(dureza) && dureza <= durezaNormaParsed;
    console.log(`⚙️ Dureza validada: ${dureza} <= ${durezaNormaParsed} ✅? ${durezaOk}`);
  }

  // Extras (Enrolamento, Dobramento, etc) - ignorado no JS por enquanto

  // Resultado final
  const aprovado = espOk && largOk && tracaoOk && durezaOk;
  console.log(`🏁 Resultado Final: ${aprovado ? "✅ Aprovado" : "❌ Reprovado"}`);

  // Atualiza visualmente
  if (espInput) {
    espInput.classList.toggle("is-valid", espOk);
    espInput.classList.toggle("is-invalid", !espOk);
  }
  if (largInput) {
    largInput.classList.toggle("is-valid", largOk);
    largInput.classList.toggle("is-invalid", !largOk);
  }
  tracaoInput.classList.toggle("is-valid", tracaoOk);
  tracaoInput.classList.toggle("is-invalid", !tracaoOk);
  durezaInput.classList.toggle("is-valid", durezaOk);
  durezaInput.classList.toggle("is-invalid", !durezaOk);

  laudoCell.innerHTML = aprovado
    ? "<span class='text-success fw-bold'>Aprovado</span>"
    : "<span class='text-danger fw-bold'>Reprovado</span>";

  atualizarStatusGeral();
}
