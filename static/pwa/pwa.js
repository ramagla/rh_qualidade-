// Lida com o prompt "Instalar app" e registra o SW
let deferredPrompt = null;

window.addEventListener("load", () => {
  // Registra o Service Worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js");
  }

  const btn = document.getElementById("btnInstallPWA");
  if (btn) {
    btn.addEventListener("click", async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      deferredPrompt = null;
      btn.style.display = "none";
      // Opcional: enviar analytics do outcome
    });
  }
});

// Captura o evento disparado pelo Chrome antes de mostrar o prompt
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const btn = document.getElementById("btnInstallPWA");
  if (btn) btn.style.display = "inline-block";
});

// Opcional: detectar quando foi instalado
window.addEventListener("appinstalled", () => {
  const btn = document.getElementById("btnInstallPWA");
  if (btn) btn.style.display = "none";
});
