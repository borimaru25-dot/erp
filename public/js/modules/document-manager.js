/**
 * Document Manager Module
 * - File upload (Excel only) → temp folder
 * - Temp save display & document list
 * - Final save with dynamic field mapping
 */
import { apiGet, apiPost, apiDelete, apiUpload } from '../core/api.js';
import { showToast, openModal, closeModal, $, $$ } from '../core/ui.js';
import {
  renderExcelSheet,
  readSheetFromDOM,
  updateToolbarFilename,
  getSheetData,
} from './excel-sheet.js';

/* ===== State ===== */
let tempFiles = [];
let finalFiles = [];
let currentFileName = '';
let currentFileSource = '';  // 'temp' | 'final'

/* ===== Init ===== */
export function init() {
  bindUploadButton();
  bindSaveButton();
  bindTabNavigation();
  bindTempSaveConfirm();
  loadTempFiles();
  loadFinalFiles();
}

// Re-export for ai-chat.js
export { renderExcelSheet } from './excel-sheet.js';

/* ===== Tab Navigation ===== */
function bindTabNavigation() {
  $$('.tab-nav__item').forEach((tab) => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      $$('.tab-nav__item').forEach((t) => t.classList.remove('is-active'));
      tab.classList.add('is-active');
      $$('.tab-pane').forEach((pane) => pane.classList.remove('is-active'));
      const pane = document.getElementById(target);
      if (pane) pane.classList.add('is-active');
    });
  });
}

/* ===== File Upload ===== */
function bindUploadButton() {
  const uploadBtn = $('#upload-btn');
  const fileInput = $('#file-input');

  if (uploadBtn) {
    uploadBtn.addEventListener('click', () => fileInput.click());
  }

  if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
  }

  const dropZone = $('#drop-zone');
  if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('is-dragover');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('is-dragover');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('is-dragover');
      const files = Array.from(e.dataTransfer.files);
      const excelFile = files.find((f) =>
        f.name.match(/\.(xlsx|xls|csv)$/i)
      );
      if (excelFile) {
        showTempSaveModal(excelFile);
      } else {
        showToast('엑셀 파일만 업로드 가능합니다.', 'error');
      }
    });
  }
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
    showToast('엑셀 파일만 업로드 가능합니다.', 'error');
    e.target.value = '';
    return;
  }
  showTempSaveModal(file);
  e.target.value = '';
}

/* ===== Temp Save Modal ===== */
let pendingFile = null;

function showTempSaveModal(file) {
  pendingFile = file;
  const nameEl = $('#modal-temp-filename');
  if (nameEl) nameEl.textContent = file.name;
  openModal('modal-temp-save');
}

function bindTempSaveConfirm() {
  const confirmBtn = $('#btn-confirm-temp-save');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      if (!pendingFile) return;
      await uploadToTemp(pendingFile);
      pendingFile = null;
      closeModal('modal-temp-save');
    });
  }
}

async function uploadToTemp(file) {
  const formData = new FormData();
  formData.append('file', file);
  try {
    await apiUpload('/files/temp-upload', formData);
    showToast('임시 저장되었습니다.', 'success');
    await loadTempFiles();
  } catch (err) {
    showToast(`업로드 실패: ${err.message}`, 'error');
  }
}

/* ===== Load & Render Temp Files ===== */
export async function loadTempFiles() {
  try {
    const data = await apiGet('/files/temp-list');
    tempFiles = data.files || [];
  } catch {
    tempFiles = [];
  }
  renderTempFileList();
}

function renderTempFileList() {
  const container = $('#temp-file-list');
  if (!container) return;

  if (tempFiles.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state__icon">📂</div>' +
      '<div class="empty-state__text">임시 저장된 파일이 없습니다</div></div>';
    updateCount('#temp-file-count', 0);
    return;
  }

  container.innerHTML = '';
  const ul = document.createElement('ul');
  ul.className = 'file-list';
  tempFiles.forEach((file) => ul.appendChild(createFileItem(file, 'temp')));
  container.appendChild(ul);
  updateCount('#temp-file-count', tempFiles.length);
}

/* ===== Load & Render Final Files ===== */
export async function loadFinalFiles() {
  try {
    const data = await apiGet('/files/final-list');
    finalFiles = data.files || [];
  } catch {
    finalFiles = [];
  }
  renderFinalFileList();
}

function renderFinalFileList() {
  const container = $('#final-file-list');
  if (!container) return;

  if (finalFiles.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state__icon">📁</div>' +
      '<div class="empty-state__text">최종본 파일이 없습니다</div></div>';
    updateCount('#final-file-count', 0);
    return;
  }

  container.innerHTML = '';
  const ul = document.createElement('ul');
  ul.className = 'file-list';
  finalFiles.forEach((file) => ul.appendChild(createFileItem(file, 'final')));
  container.appendChild(ul);
  updateCount('#final-file-count', finalFiles.length);
}

/* ===== Shared File Item Builder ===== */
function createFileItem(file, source) {
  const li = document.createElement('li');
  li.className = 'file-item';
  if (currentFileName === file.name && currentFileSource === source) {
    li.classList.add('is-selected');
  }

  const icon = source === 'temp' ? '📄' : '📋';
  const saveAction = source === 'temp' ? 'save-final' : 'save-excel';
  const deleteAction = source === 'temp' ? 'delete-temp' : 'delete-final';

  li.innerHTML =
    `<span class="file-item__icon">${icon}</span>` +
    `<span class="file-item__name">${escapeHtml(file.name)}</span>` +
    `<span class="file-item__date">${formatDate(file.created_at)}</span>` +
    '<span class="file-item__actions">' +
      `<button class="btn btn--sm btn--success" data-action="${saveAction}">` +
      '저장</button>' +
      `<button class="btn btn--sm btn--danger" data-action="${deleteAction}">` +
      '삭제</button>' +
    '</span>';

  li.querySelector('.file-item__name')
    .addEventListener('click', () => loadFileToSheet(file, source));

  li.querySelector(`[data-action="${saveAction}"]`)
    .addEventListener('click', (e) => {
      e.stopPropagation();
      if (source === 'temp') saveToFinal(file);
      else saveToExcelFile(file.id);
    });

  li.querySelector(`[data-action="${deleteAction}"]`)
    .addEventListener('click', (e) => {
      e.stopPropagation();
      if (source === 'temp') deleteTempFile(file.id);
      else deleteFinalFile(file.id);
    });

  return li;
}

/* ===== File Operations ===== */
async function loadFileToSheet(file, source) {
  try {
    const data = await apiGet(`/files/${source}/${file.id}`);
    currentFileName = file.name;
    currentFileSource = source;
    renderExcelSheet(data);
    updateToolbarFilename(file.name);
    if (source === 'temp') renderTempFileList();
    else renderFinalFileList();
  } catch (err) {
    showToast(`파일 로드 실패: ${err.message}`, 'error');
  }
}

async function saveToFinal(file) {
  try {
    await apiPost('/files/save-final', { file_id: file.id });
    showToast('최종본으로 저장되었습니다.', 'success');
    await loadTempFiles();
    await loadFinalFiles();
  } catch (err) {
    showToast(`저장 실패: ${err.message}`, 'error');
  }
}

async function deleteTempFile(fileId) {
  try {
    await apiDelete(`/files/temp/${fileId}`);
    showToast('임시 파일이 삭제되었습니다.', 'success');
    await loadTempFiles();
  } catch (err) {
    showToast(`삭제 실패: ${err.message}`, 'error');
  }
}

async function deleteFinalFile(fileId) {
  try {
    await apiDelete(`/files/final/${fileId}`);
    showToast('최종본이 삭제되었습니다.', 'success');
    await loadFinalFiles();
  } catch (err) {
    showToast(`삭제 실패: ${err.message}`, 'error');
  }
}

async function saveToExcelFile(fileId) {
  try {
    const data = await apiPost('/files/save-excel', { file_id: fileId });
    if (data.download_url) {
      const a = document.createElement('a');
      a.href = data.download_url;
      a.download = '';
      a.click();
    }
    showToast('엑셀 파일로 저장되었습니다.', 'success');
  } catch (err) {
    showToast(`저장 실패: ${err.message}`, 'error');
  }
}

/* ===== Excel Sheet Save Button ===== */
function bindSaveButton() {
  const saveBtn = $('#save-excel-btn');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      if (!getSheetData()) {
        showToast('저장할 데이터가 없습니다.', 'warning');
        return;
      }
      try {
        await apiPost('/files/save-excel-data', {
          filename: currentFileName,
          data: readSheetFromDOM(),
        });
        showToast('엑셀 파일로 저장되었습니다.', 'success');
      } catch (err) {
        showToast(`저장 실패: ${err.message}`, 'error');
      }
    });
  }
}

/* ===== Utilities ===== */
function updateCount(selector, count) {
  const el = $(selector);
  if (el) el.textContent = count;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mi = String(d.getMinutes()).padStart(2, '0');
  return `${mm}/${dd} ${hh}:${mi}`;
}
