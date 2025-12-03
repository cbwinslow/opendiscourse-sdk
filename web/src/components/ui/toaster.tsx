import * as React from 'react';

export function Toaster() {
  return (
    <div
      id="toast-container"
      className="fixed bottom-0 right-0 z-50 flex flex-col gap-2 p-4"
    />
  );
}

export function toast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toastEl = document.createElement('div');
  toastEl.className = `
    max-w-sm p-4 rounded-lg shadow-lg transform transition-all duration-300 ease-in-out
    ${type === 'success' ? 'bg-green-500 text-white' : ''}
    ${type === 'error' ? 'bg-red-500 text-white' : ''}
    ${type === 'info' ? 'bg-blue-500 text-white' : ''}
  `;
  toastEl.textContent = message;

  container.appendChild(toastEl);

  // Auto remove after 5 seconds
  setTimeout(() => {
    toastEl.style.opacity = '0';
    toastEl.style.transform = 'translateX(100%)';
    setTimeout(() => {
      if (container.contains(toastEl)) {
        container.removeChild(toastEl);
      }
    }, 300);
  }, 5000);
}