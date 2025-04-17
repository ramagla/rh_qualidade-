document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[id^="bitola_"], input[id^="tracao_"], input[id^="dureza_"]').forEach(input => {
    const id = input.id.split("_")[1];
    input.addEventListener("input", () => validarBitolaETracao(id));
  });

  document.querySelectorAll('select[name^="rolos-"]').forEach(select => {
    const match = select.name.match(/^rolos-(\d+)-/);
    if (match) {
      const index = match[1];
      select.addEventListener("change", () => {
        const roloId = document.querySelector(`input[name="rolos-${index}-id"]`)?.value;
        if (roloId) validarBitolaETracao(roloId);
      });
    }
  });

  document.querySelectorAll('.encontrado-input').forEach(input => {
    input.addEventListener("input", function () {
      const row = input.closest("tr");
      const min = parseFloat(row.querySelector(".min-hidden").value.replace(",", ".")) || 0;
      const max = parseFloat(row.querySelector(".max-hidden").value.replace(",", ".")) || 0;
      const valor = parseFloat(input.value.replace(",", "."));
      const laudo = row.querySelector(".laudo");

      input.classList.remove("is-valid", "is-invalid");
      laudo.classList.remove("text-success", "text-danger");

      if (isNaN(valor)) {
        laudo.innerText = "—";
        return;
      }

      const aprovado = (min === 0 && max === 0) || (min === 0 && valor <= max) || (valor >= min && valor <= max);

      if (aprovado) {
        input.classList.add("is-valid");
        laudo.innerText = "Aprovado";
        laudo.classList.add("text-success");
      } else {
        input.classList.add("is-invalid");
        laudo.innerText = "Reprovado";
        laudo.classList.add("text-danger");
      }

      atualizarStatusGeral();
    });
  });

  const flagManual = document.getElementById("switchStatusManual");
  if (flagManual) {
    flagManual.addEventListener("change", () => toggleStatusManual(flagManual));
  }

  atualizarStatusGeral();
});
