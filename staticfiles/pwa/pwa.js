// pwa.js — registro do SW e controle do botão
(function () {
  function registerServiceWorker() {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/service-worker.js")
        .then(() => console.log("[PWA] SW registrado"))
        .catch((err) => console.error("[PWA] Falha ao registrar SW:", err));
    }
  }

  function setupInstallButton() {
    const btn = document.getElementById("btnInstallPWA");
    if (!btn) return;

    btn.addEventListener("click", async () => {
      // usa o evento capturado no inline do <head>
      const dp = window._deferredPrompt;
      if (!dp) {
        // motivos comuns: app não está “installable” ainda
        console.warn("[PWA] beforeinstallprompt ainda não disponível.");
        alert("O navegador ainda não liberou a instalação.\n\nVerifique em Application ▸ Manifest se está Installable = Yes (ícones 192/512, start_url, SW ativo).");
        return;
      }
      dp.prompt();
      const { outcome } = await dp.userChoice;
      console.log("[PWA] Instalação:", outcome);
      window._deferredPrompt = null;
      // opcional: esconder botão após a tentativa
      // btn.style.display = "none";
    });
  }

  // Esconde botão se já estiver instalado (PWA rodando)
  function hideIfStandalone() {
    const inStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                         window.navigator.standalone === true;
    if (inStandalone) {
      const btn = document.getElementById("btnInstallPWA");
      if (btn) btn.style.display = "none";
    }
  }

  window.addEventListener("load", () => {
    registerServiceWorker();
    setupInstallButton();
    hideIfStandalone();
  });

  // Quando instalar, esconde o botão
  window.addEventListener("appinstalled", () => {
    const btn = document.getElementById("btnInstallPWA");
    if (btn) btn.style.display = "none";
    console.log("[PWA] App instalado");
  });
})();
