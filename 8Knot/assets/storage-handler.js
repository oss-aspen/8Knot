// Browser storage error handling and capacity testing
// This script handles quota exceeded errors and tests storage capacity

// Listen for storage quota exceeded errors
window.addEventListener('error', function(event) {
    if (event.message && event.message.toLowerCase().includes('quota') &&
        event.message.toLowerCase().includes('exceeded')) {
        var warningEl = document.getElementById('storage-quota-warning');
        if (warningEl) {
            warningEl.style.display = 'block';
        }
    }
});

// Test storage capacity on page load
(function() {
    try {
        var testKey = 'storage_test';
        var testString = new Array(512 * 1024).join('a');  // 512KB
        sessionStorage.setItem(testKey, testString);
        sessionStorage.removeItem(testKey);
    } catch (e) {
        if (e.name === 'QuotaExceededError' ||
            (e.message &&
            (e.message.toLowerCase().includes('quota') ||
             e.message.toLowerCase().includes('exceeded')))) {
            var warningEl = document.getElementById('storage-quota-warning');
            if (warningEl) {
                warningEl.style.display = 'block';
            }
        }
    }
})(); 