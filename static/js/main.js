// Main JavaScript file
document.addEventListener('DOMContentLoaded', () => {
    // Basic initialization
});

// Global toast notification function
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error' || type === 'danger') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span>${message}</span>
        <button class="toast-close" aria-label="Close">&times;</button>
    `;

    container.appendChild(toast);

    // Close button click
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        removeToast(toast);
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 5000);
}

function removeToast(toast) {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}
