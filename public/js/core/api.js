/**
 * API fetch wrapper — no auth required.
 */

const BASE_URL = '/api';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

export async function apiGet(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: JSON_HEADERS,
  });
  return handleResponse(res);
}

export async function apiPost(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function apiDelete(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'DELETE',
    headers: JSON_HEADERS,
  });
  return handleResponse(res);
}

export async function apiUpload(path, formData) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}

async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}
