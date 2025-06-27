function toggleStatusManual(checkbox) {
  const campoObs = document.getElementById("campoObsManual");
  if (campoObs) {
    campoObs.style.display = checkbox.checked ? "block" : "none";
  }
  atualizarStatusGeral();
}
