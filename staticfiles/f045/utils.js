const fatorConversao = 0.10197;

function formatarValor(valor) {
  return valor.toFixed(4).replace(".", ",");
}

function arredondar(valor) {
  return Math.round((valor + Number.EPSILON) * 100) / 100;
}
