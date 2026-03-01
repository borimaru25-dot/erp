/**
 * Authentication: login, logout, session check.
 */
import { apiPost } from './api.js';

export function isLoggedIn() {
  return !!localStorage.getItem('auth_token');
}

export async function login(email, password) {
  const data = await apiPost('/auth/login', { email, password });
  localStorage.setItem('auth_token', data.token);
  return data;
}

export async function logout() {
  try {
    await apiPost('/auth/logout', {});
  } finally {
    localStorage.removeItem('auth_token');
    window.location.hash = '#/login';
  }
}

export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.hash = '#/login';
    return false;
  }
  return true;
}
