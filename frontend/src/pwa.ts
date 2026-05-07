/**
 * Service worker registration for PWA offline support.
 * 
 * Only registers in production builds. Development mode uses Vite's HMR.
 */

export function registerServiceWorker(): void {
  if (import.meta.env.DEV) {
    console.log("[PWA] Skipping service worker in development mode");
    return;
  }

  if (!("serviceWorker" in navigator)) {
    console.warn("[PWA] Service workers not supported in this browser");
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .then((registration) => {
        console.log("[PWA] Service worker registered:", registration.scope);

        // Check for updates every hour
        setInterval(
          () => {
            registration.update();
          },
          60 * 60 * 1000,
        );
      })
      .catch((error) => {
        console.error("[PWA] Service worker registration failed:", error);
      });
  });

  // Notify user when new version is available
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    console.log("[PWA] New version available — reload to update");
    // You could show a toast notification here
  });
}
