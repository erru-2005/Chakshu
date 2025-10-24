// Notification and success animation system
let activeNotifications = 0;
const maxNotifications = 3; // Maximum number of visible notifications

/**
 * Show a notification with optional animation
 * @param {string} message - The message to display
 * @param {string} type - success, error, warning, or info
 * @param {boolean} animate - Whether to show animation (for success/error)
 * @param {number} duration - How long to show the notification in ms
 */
function showNotification(message, type = 'info', animate = false, duration = 4000) {
    // Check if we already have too many notifications
    if (activeNotifications >= maxNotifications) {
        // Remove the oldest notification
        const notifications = document.querySelectorAll('.notification');
        if (notifications.length > 0) {
            notifications[0].remove();
            activeNotifications--;
        }
    }

    // Create container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}${animate ? ' with-animation' : ''}`;
    
    // Add animation element if needed
    if (animate) {
        const animationEl = document.createElement('div');
        if (type === 'success') {
            animationEl.className = 'success-animation';
            animationEl.innerHTML = `
                <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
            `;
        } else if (type === 'error') {
            animationEl.className = 'error-animation';
            animationEl.innerHTML = `
                <svg class="crossmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="crossmark-circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="crossmark-x" fill="none" d="M16 16 36 36 M36 16 16 36"/>
                </svg>
            `;
        }
        notification.appendChild(animationEl);
    }

    // Add message
    const messageEl = document.createElement('div');
    messageEl.className = 'notification-message';
    messageEl.textContent = message;
    notification.appendChild(messageEl);

    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = function() {
        notification.classList.add('notification-hiding');
        setTimeout(() => {
            notification.remove();
            activeNotifications--;
        }, 300);
    };
    notification.appendChild(closeBtn);

    // Add to container
    container.appendChild(notification);
    activeNotifications++;

    // Add visible class to trigger animation
    setTimeout(() => {
        notification.classList.add('notification-visible');
    }, 10);

    // Auto-remove after duration
    if (duration) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('notification-hiding');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                        activeNotifications--;
                    }
                }, 300);
            }
        }, duration);
    }
}

/**
 * Show a success notification with animation
 */
function showSuccess(message, animate = true) {
    showNotification(message, 'success', animate);
}

/**
 * Show an error notification
 */
function showError(message, animate = false) {
    showNotification(message, 'error', animate);
}

/**
 * Show a warning notification
 */
function showWarning(message) {
    showNotification(message, 'warning', false);
}

/**
 * Show an info notification
 */
function showInfo(message) {
    showNotification(message, 'info', false);
} 