// toggle_unidade_tracao.js
const FATOR_CONVERSAO = 0.10197;

function formatarValor(v) {
  return v.toFixed(2).replace('.', ',');
}

function toggleUnidadeTracao(switchEl) {
  const emMpa = switchEl.checked;
  console.log('[toggleUnidadeTracao] emMpa =', emMpa);

  // cabeçalhos
  document.getElementById('th_rmin').textContent = emMpa
    ? 'R. Mín (MPa)' : 'R. Mín (Kgf/mm²)';
  document.getElementById('th_rmax').textContent = emMpa
    ? 'R. Máx (MPa)' : 'R. Máx (Kgf/mm²)';

  // células rmin / rmax
  ['rmin','rmax'].forEach(pref => {
    document.querySelectorAll(`td[id^="${pref}_"]`).forEach(cell => {
      const id = cell.id.replace(`${pref}_`, '');
      const orig = parseFloat(
        document.getElementById(`${pref}_valor_${id}`)
                .value.replace(',', '.')
      );
      if (!isNaN(orig)) {
        const conv = emMpa
          ? orig / FATOR_CONVERSAO
          : orig;
        cell.textContent = formatarValor(conv);
      }
    });
  });

  // e converta também os inputs de tração (valor visual)
  document.querySelectorAll('input[id^="tracao_"]').forEach(input => {
    // guarde o bruto uma única vez
    if (!input.dataset.original) {
      input.dataset.original = input.value;
    }
    const bruto = parseFloat(input.dataset.original.replace(',', '.'));
    if (!isNaN(bruto)) {
      const conv = emMpa
        ? (bruto / FATOR_CONVERSAO)
        : bruto;
      input.value = formatarValor(conv);
    }
    // revalide o rolo para atualizar o laudo visual
    const id = input.id.split('_')[1];
    validarBitolaETracao(id);
  });
}
