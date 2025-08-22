// toggle_unidade_tracao.js — revalida rolos e certificado, com logs
const FATOR_CONVERSAO = 0.10197;

function formatarValor(v) {
  return v.toFixed(2).replace('.', ',');
}

function toggleUnidadeTracao(switchEl) {
  const emMpa = switchEl.checked === true;
  console.log("[F045/ToggleUnidade] MPa?", emMpa);

  // Cabeçalhos
  const thMin = document.getElementById('th_rmin');
  const thMax = document.getElementById('th_rmax');
  if (thMin) thMin.textContent = emMpa ? 'R. Mín (MPa)' : 'R. Mín (Kgf/mm²)';
  if (thMax) thMax.textContent = emMpa ? 'R. Máx (MPa)' : 'R. Máx (Kgf/mm²)';

  // Células rmin/rmax
  ['rmin','rmax'].forEach(pref => {
    document.querySelectorAll(`td[id^="${pref}_"]`).forEach(cell => {
      const id = cell.id.replace(`${pref}_`, '');
      const orig = parseFloat(
        document.getElementById(`${pref}_valor_${id}`)
                .value.replace(',', '.')
      );
      if (!isNaN(orig)) {
        const conv = emMpa ? (orig / FATOR_CONVERSAO) : orig;
        cell.textContent = formatarValor(conv);
      }
    });
  });

  // Inputs de tração dos rolos (visual) + revalidação
  document.querySelectorAll('input[id^="tracao_"]').forEach(input => {
    if (!input.dataset.original) input.dataset.original = input.value;
    const bruto = parseFloat(String(input.dataset.original).replace(',', '.'));
    if (!isNaN(bruto)) {
      const conv = emMpa ? (bruto / FATOR_CONVERSAO) : bruto;
      input.value = formatarValor(conv);
    }
    const id = input.id.split('_')[1];
    if (typeof validarBitolaETracao === 'function') validarBitolaETracao(id);
  });

  // Revalida o certificado também
  if (typeof window.__f045_validarCertificado === 'function') {
    console.log("[F045/ToggleUnidade] Revalidando certificado…");
    window.__f045_validarCertificado();
  }
}
