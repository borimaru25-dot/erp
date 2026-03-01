/**
 * AI Wizard Module
 * - Generate PPT slides from Excel data (AI슬라이드-display)
 * - Generate approval documents (AI결재-display)
 */
import { apiPost } from '../core/api.js';
import { showToast, openModal, closeModal, $ } from '../core/ui.js';
import { getChatHistory } from './ai-chat.js';

export function init() {
  bindWizardButton();
  bindSlideGenerate();
  bindApprovalGenerate();
}

function bindWizardButton() {
  const btn = $('#btn-ai-wizard');
  if (btn) {
    btn.addEventListener('click', () => {
      openModal('modal-ai-wizard');
    });
  }
}

/* ===== Slide Generation ===== */
function bindSlideGenerate() {
  const btn = $('#btn-generate-slides');
  if (btn) {
    btn.addEventListener('click', generateSlides);
  }
}

async function generateSlides() {
  const slideContainer = $('#slide-preview');
  if (!slideContainer) return;

  slideContainer.innerHTML =
    '<div class="empty-state"><div class="spinner"></div>' +
    '<div class="empty-state__text">슬라이드 생성 중...</div></div>';

  try {
    const sheetData = getExcelDataFromDOM();
    const history = getChatHistory();

    const result = await apiPost('/ai/generate-slides', {
      excel_data: sheetData,
      chat_history: history.slice(-5),
    });

    renderSlides(result.slides || []);
    showToast('슬라이드가 생성되었습니다.', 'success');
  } catch (err) {
    slideContainer.innerHTML =
      '<div class="empty-state">' +
      '<div class="empty-state__icon">⚠️</div>' +
      `<div class="empty-state__text">생성 실패: ${err.message}</div></div>`;
  }
}

function renderSlides(slides) {
  const container = $('#slide-preview');
  if (!container) return;

  if (slides.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state__icon">📽️</div>' +
      '<div class="empty-state__text">생성된 슬라이드가 없습니다</div></div>';
    return;
  }

  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'slide-preview';

  slides.forEach((slide, idx) => {
    const card = document.createElement('div');
    card.className = 'slide-card';
    card.innerHTML =
      `<div><strong>슬라이드 ${idx + 1}</strong>` +
      `<div>${escapeHtml(slide.title || '')}</div>` +
      `<div>${escapeHtml(slide.content || '')}</div></div>`;
    wrapper.appendChild(card);
  });

  container.appendChild(wrapper);
}

/* ===== Approval Document Generation ===== */
function bindApprovalGenerate() {
  const btn = $('#btn-generate-approval');
  if (btn) {
    btn.addEventListener('click', generateApproval);
  }
}

async function generateApproval() {
  const approvalContainer = $('#approval-preview');
  if (!approvalContainer) return;

  approvalContainer.innerHTML =
    '<div class="empty-state"><div class="spinner"></div>' +
    '<div class="empty-state__text">결재 문서 생성 중...</div></div>';

  try {
    const sheetData = getExcelDataFromDOM();
    const history = getChatHistory();

    const result = await apiPost('/ai/generate-approval', {
      excel_data: sheetData,
      chat_history: history.slice(-5),
    });

    renderApproval(result.document || {});
    showToast('결재 문서가 생성되었습니다.', 'success');
  } catch (err) {
    approvalContainer.innerHTML =
      '<div class="empty-state">' +
      '<div class="empty-state__icon">⚠️</div>' +
      `<div class="empty-state__text">생성 실패: ${err.message}</div></div>`;
  }
}

function renderApproval(doc) {
  const container = $('#approval-preview');
  if (!container) return;

  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'approval-doc';

  const title = document.createElement('div');
  title.className = 'approval-doc__title';
  title.textContent = doc.title || '결재 문서';
  wrapper.appendChild(title);

  const fields = doc.fields || [];
  fields.forEach((field) => {
    const row = document.createElement('div');
    row.className = 'approval-doc__field';
    row.innerHTML =
      `<span class="approval-doc__label">${escapeHtml(field.label)}</span>` +
      `<span class="approval-doc__value">${escapeHtml(field.value)}</span>`;
    wrapper.appendChild(row);
  });

  container.appendChild(wrapper);
}

/* ===== Helpers ===== */
function getExcelDataFromDOM() {
  const table = document.querySelector('.excel-table');
  if (!table) return null;

  const headers = [];
  const headerCells = table.querySelectorAll('thead th');
  headerCells.forEach((th, idx) => {
    if (idx > 0) headers.push(th.textContent);
  });

  const rows = [];
  table.querySelectorAll('tbody tr').forEach((tr) => {
    const row = [];
    tr.querySelectorAll('td').forEach((td, idx) => {
      if (idx > 0) row.push(td.textContent);
    });
    rows.push(row);
  });

  return { headers, rows };
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
