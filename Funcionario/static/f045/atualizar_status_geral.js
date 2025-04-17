function atualizarStatusGeral() {
  const laudosComposicao = [...document.querySelectorAll(".laudo")];
  const laudosRolos = [...document.querySelectorAll('td[id^="laudo_"]')];

  const todosAprovados = [...laudosComposicao, ...laudosRolos].every(cell =>
    cell.textContent.includes("Aprovado") && !cell.textContent.includes("Condicionalmente")
  );

  const geral = document.getElementById("status_geral");
  const flagManual = document.getElementById("switchStatusManual");
  const hiddenInput = document.getElementById("status_geral_hidden");

  if (flagManual && flagManual.checked) {
    geral.className = "form-control fw-bold text-center text-warning";
    geral.innerHTML = "Aprovação Condicional ⚠️";
    hiddenInput.value = "Aprovação Condicional";
  } else if (todosAprovados) {
    geral.className = "form-control fw-bold text-center text-success";
    geral.innerHTML = "Aprovado ✅";
    hiddenInput.value = "Aprovado";
  } else {
    geral.className = "form-control fw-bold text-center text-danger";
    geral.innerHTML = "Reprovado ❌";
    hiddenInput.value = "Reprovado";
  }
}
