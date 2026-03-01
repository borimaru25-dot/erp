/**
 * Document Manager page initialization.
 * Entry point that imports and initializes all sub-modules.
 */
import { initModalCloseButtons } from '../core/ui.js';
import * as docManager from './document-manager.js';
import * as aiChat from './ai-chat.js';
import * as aiWizard from './ai-wizard.js';

document.addEventListener('DOMContentLoaded', () => {
  initModalCloseButtons();
  docManager.init();
  aiChat.init();
  aiWizard.init();
  initWizardTabs();
});

function initWizardTabs() {
  const wizardBody = document.getElementById('wizard-body');
  if (!wizardBody) return;

  wizardBody.querySelectorAll('.tab-nav__item').forEach((tab) => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      wizardBody.querySelectorAll('.tab-nav__item')
        .forEach((t) => t.classList.remove('is-active'));
      tab.classList.add('is-active');
      wizardBody.querySelectorAll('.tab-pane')
        .forEach((pane) => pane.classList.remove('is-active'));
      const pane = document.getElementById(target);
      if (pane) pane.classList.add('is-active');
    });
  });
}
