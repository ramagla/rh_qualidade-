(function () {
  function registerSW() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js')
        .then(() => console.log('[PWA] SW registrado'))
        .catch(err => console.error('[PWA] SW erro:', err));
    }
  }

  function setupBtn() {
    const btn = document.getElementById('btnInstallPWA');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      if (!navigator.serviceWorker.controller) {
        alert('Atualize a página para ativar o Service Worker e tente novamente.');
        return;
      }
      const dp = window._deferredPrompt;
      if (!dp) {
        alert('O navegador ainda não liberou a instalação.\nVerifique em Application ▸ Manifest se está Installable = Yes.');
        return;
      }
      dp.prompt();
      const { outcome } = await dp.userChoice;
      console.log('[PWA] Instalação:', outcome);
      window._deferredPrompt = null;
      // btn.style.display = 'none'; // opcional
    });
  }

  window.addEventListener('load', () => {
    registerSW();
    setupBtn();
  });

  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App instalado');
    const btn = document.getElementById('btnInstallPWA');
    if (btn) btn.style.display = 'none';
  });
})();
