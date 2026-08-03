(function initializePwa() {
  const head = document.head;
  if (!head.querySelector('link[rel="manifest"]')) {
    const manifest = document.createElement('link');
    manifest.rel = 'manifest';
    manifest.href = '../manifest.webmanifest';
    head.appendChild(manifest);
  }
  if (!head.querySelector('meta[name="theme-color"]')) {
    const theme = document.createElement('meta');
    theme.name = 'theme-color';
    theme.content = '#1f5136';
    head.appendChild(theme);
  }
  const apple = document.createElement('meta');
  apple.name = 'apple-mobile-web-app-capable';
  apple.content = 'yes';
  head.appendChild(apple);

  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('../sw.js', { scope: '../' }).catch(error => {
        console.warn('PWA service worker registration failed', error);
      });
    });
  }

  let installPrompt = null;
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    document.querySelectorAll('[data-install-app]').forEach(button => {
      button.hidden = false;
    });
  });

  window.installMaizeApp = async function installMaizeApp() {
    if (installPrompt) {
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      document.querySelectorAll('[data-install-app]').forEach(button => {
        button.hidden = true;
      });
      return;
    }
    const isiOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
    alert(isiOS
      ? 'In Safari, tap Share, then “Add to Home Screen”.\n在 Safari 中点“分享”，再选择“添加到主屏幕”。'
      : 'Use your browser menu and choose “Install app” or “Add to Home screen”.\n请打开浏览器菜单，选择“安装应用”或“添加到主屏幕”。');
  };
})();
