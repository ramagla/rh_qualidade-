const meses = precalculosPorMes.map(item => new Date(item.mes).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' }));
const totais = precalculosPorMes.map(item => item.total);

new Chart(document.getElementById("graficoPrecalculoMes"), {
  type: "bar",
  data: {
    labels: meses,
    datasets: [{
      label: "Pré-Cálculos por Mês",
      data: totais,
      backgroundColor: "#007bff"
    }]
  }
});
