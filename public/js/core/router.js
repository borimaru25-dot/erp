/**
 * Simple hash-based SPA router.
 */

const routes = new Map();
let currentCleanup = null;

export function registerRoute(hash, handler) {
  routes.set(hash, handler);
}

export function navigateTo(hash) {
  window.location.hash = hash;
}

export function initRouter() {
  window.addEventListener('hashchange', handleRoute);
  handleRoute();
}

async function handleRoute() {
  if (typeof currentCleanup === 'function') {
    currentCleanup();
    currentCleanup = null;
  }

  const hash = window.location.hash || '#/';
  const handler = routes.get(hash) || routes.get('#/');

  if (handler) {
    currentCleanup = await handler();
  }
}
