/**
 * AI Chat Module
 * - Chat input → AI processing → AI chat display
 * - AI results → Excel sheet modification
 * - AI results → Checklist update
 */
import { apiPost } from '../core/api.js';
import { showToast, $ } from '../core/ui.js';
import { renderExcelSheet } from './excel-sheet.js';

let chatHistory = [];

export function init() {
  bindChatInput();
}

function bindChatInput() {
  const input = $('#chat-input');
  const sendBtn = $('#chat-send-btn');

  if (sendBtn) {
    sendBtn.addEventListener('click', () => sendMessage());
  }

  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
}

async function sendMessage() {
  const input = $('#chat-input');
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  appendMessage('user', text);
  chatHistory.push({ role: 'user', content: text });

  appendTypingIndicator();

  try {
    const result = await apiPost('/ai/chat', {
      message: text,
      history: chatHistory.slice(-10),
    });

    removeTypingIndicator();

    const aiMessage = result.message || '응답을 생성할 수 없습니다.';
    appendMessage('ai', aiMessage);
    chatHistory.push({ role: 'assistant', content: aiMessage });

    // If AI returns Excel data, render it
    if (result.excel_data) {
      renderExcelSheet(result.excel_data);
      showToast('AI가 엑셀 데이터를 업데이트했습니다.', 'info');
    }
  } catch (err) {
    removeTypingIndicator();
    appendMessage('ai', `오류가 발생했습니다: ${err.message}`);
  }
}

function appendMessage(role, content) {
  const container = $('#chat-messages');
  if (!container) return;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble chat-bubble--${role}`;
  bubble.textContent = content;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = $('#chat-messages');
  if (!container) return;

  const indicator = document.createElement('div');
  indicator.className = 'chat-bubble chat-bubble--ai';
  indicator.id = 'typing-indicator';
  indicator.innerHTML = '<div class="spinner"></div>';
  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

export function getChatHistory() {
  return chatHistory;
}
