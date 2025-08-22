// atualizar_status_geral.js — considera .laudo, laudos dos rolos e o laudo do certificado (div ou input), com logs
function atualizarStatusGeral() {
  const getTxt = (el) => {
    if (!el) return "";
    const tag = el.tagName?.toLowerCase();
    return (tag === "input" || tag === "textarea") ? (el.value || "") : (el.textContent || "");
  };

  const laudosComposicao = [...document.querySelectorAll(".laudo")];
  const laudosRolos = [...document.querySelectorAll('td[id^="laudo_"]')];

  // Laudo do certificado pode ser <div> ou <input>
  const laudoCert = document.getElementById("laudo_certificado");

  const todos = laudoCert
    ? [...laudosComposicao, ...laudosRolos, laudoCert]
    : [...laudosComposicao, ...laudosRolos];

  const todosAprovados = todos.every((cell) => {
    const t = getTxt(cell);
    return t.includes("Aprovado") && !t.includes("Condicionalmente");
  });

  console.log("[F045/Status] laudos considerados:", {
    qtd: todos.length,
    textos: todos.map(getTxt)
  });

  const geral = document.getElementById("status_geral");
  const flagManual = document.getElementById("switchStatusManual");
  const hiddenInput = document.getElementById("status_geral_hidden");

  if (flagManual && flagManual.checked) {
    geral.className = "form-control fw-bold text-center text-warning";
    geral.innerHTML = "Aprovação Condicional ⚠️";
    if (hiddenInput) hiddenInput.value = "Aprovação Condicional";
  } else if (todosAprovados) {
    geral.className = "form-control fw-bold text-center text-success";
    geral.innerHTML = "Aprovado ✅";
    if (hiddenInput) hiddenInput.value = "Aprovado";
  } else {
    geral.className = "form-control fw-bold text-center text-danger";
    geral.innerHTML = "Reprovado ❌";
    if (hiddenInput) hiddenInput.value = "Reprovado";
  }
}
