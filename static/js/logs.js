// 日誌頁面專用 JavaScript - logs.js

function refreshLogs() {
    location.reload();
}

function clearLogs() {
    // 從容器元素獲取翻譯文字
    const container = document.querySelector('.container-fluid');
    const confirmMessage = container?.dataset.confirmClearLogs || '確定要清除所有日誌嗎？此操作無法撤銷。';
    const successMessage = container?.dataset.logsClearedSuccessfully || '日誌已成功清除';
    const errorMessage = container?.dataset.errorClearingLogs || '清除日誌時發生錯誤';
    
    if (confirm(confirmMessage)) {
        fetch('/admin/clear-logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': 'fish_admin_2023'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(successMessage);
                location.reload();
            } else {
                alert(errorMessage);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(errorMessage);
        });
    }
}

function resetFilter() {
    const form = document.getElementById('filterForm');
    if (form) {
        form.reset();
        // 從容器元素獲取今天的日期
        const container = document.querySelector('.container-fluid');
        const today = container?.dataset.today || new Date().toISOString().split('T')[0];
        
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        
        if (dateFromInput) dateFromInput.value = today;
        if (dateToInput) dateToInput.value = today;
    }
}

// 當 DOM 載入完成後執行
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const params = new URLSearchParams(formData);
            
            // 根據當前路由決定跳轉目標
            const currentPath = window.location.pathname;
            if (currentPath.includes('/admin/logs')) {
                window.location.href = '/admin/logs?admin_key=fish_admin_2023&' + params.toString();
            } else {
                window.location.href = '/log?' + params.toString();
            }
        });
    }
});
