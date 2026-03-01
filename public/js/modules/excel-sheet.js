/**
 * Excel Sheet rendering and cell editing.
 * Separated from document-manager.js per Rule 5 (500-line limit).
 */
import { $ } from '../core/ui.js';

let currentSheetData = null;

export function setSheetData(data) {
  currentSheetData = data;
}

export function getSheetData() {
  return currentSheetData;
}

export function renderExcelSheet(data) {
  currentSheetData = data;
  const wrapper = $('#excel-sheet-wrapper');
  if (!wrapper) return;

  if (!data || !data.headers || !data.rows) {
    wrapper.innerHTML =
      '<div class="empty-state"><div class="empty-state__icon">📊</div>' +
      '<div class="empty-state__text">파일을 선택하여 내용을 확인하세요' +
      '</div></div>';
    return;
  }

  const table = document.createElement('table');
  table.className = 'excel-table';

  // Header row
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  const thIndex = document.createElement('th');
  thIndex.className = 'row-header';
  thIndex.textContent = '#';
  headerRow.appendChild(thIndex);

  data.headers.forEach((header) => {
    const th = document.createElement('th');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Data rows
  const tbody = document.createElement('tbody');
  data.rows.forEach((row, rowIdx) => {
    const tr = document.createElement('tr');
    const tdIndex = document.createElement('td');
    tdIndex.className = 'row-header';
    tdIndex.textContent = rowIdx + 1;
    tr.appendChild(tdIndex);

    data.headers.forEach((_, colIdx) => {
      const td = document.createElement('td');
      td.textContent = row[colIdx] != null ? row[colIdx] : '';
      td.dataset.row = rowIdx;
      td.dataset.col = colIdx;
      td.addEventListener('dblclick', () => startCellEdit(td));
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  wrapper.innerHTML = '';
  wrapper.appendChild(table);

  updateChecklist(data);
}

function startCellEdit(td) {
  if (td.classList.contains('is-editing')) return;
  const oldValue = td.textContent;
  td.classList.add('is-editing');
  const input = document.createElement('input');
  input.className = 'cell-input';
  input.value = oldValue;
  td.textContent = '';
  td.appendChild(input);
  input.focus();

  input.addEventListener('blur', () => finishCellEdit(td, input, oldValue));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') input.blur();
    if (e.key === 'Escape') {
      input.value = oldValue;
      input.blur();
    }
  });
}

function finishCellEdit(td, input, oldValue) {
  const newValue = input.value;
  td.classList.remove('is-editing');
  td.textContent = newValue;

  if (newValue !== oldValue && currentSheetData) {
    const row = parseInt(td.dataset.row, 10);
    const col = parseInt(td.dataset.col, 10);
    if (currentSheetData.rows[row]) {
      currentSheetData.rows[row][col] = newValue;
    }
    updateChecklist(currentSheetData);
  }
}

export function readSheetFromDOM() {
  if (!currentSheetData) return null;
  return {
    headers: currentSheetData.headers,
    rows: currentSheetData.rows,
  };
}

export function updateToolbarFilename(name) {
  const el = $('#toolbar-filename');
  if (el) el.textContent = name || '';
}

function updateChecklist(data) {
  const container = $('#checklist-body');
  if (!container || !data || !data.headers) return;

  container.innerHTML = '';
  const ul = document.createElement('ul');
  ul.className = 'checklist';

  data.headers.forEach((header, idx) => {
    const hasData = data.rows.some(
      (row) => row[idx] != null && row[idx] !== ''
    );
    const li = document.createElement('li');
    li.className = 'checklist__item';
    li.innerHTML =
      `<input type="checkbox" class="checklist__checkbox"` +
      ` ${hasData ? 'checked' : ''} disabled>` +
      `<span>${escapeHtml(header)}</span>` +
      `<span class="badge badge--${hasData ? 'success' : 'warning'}">` +
      `${hasData ? '입력됨' : '미입력'}</span>`;
    ul.appendChild(li);
  });

  container.appendChild(ul);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
