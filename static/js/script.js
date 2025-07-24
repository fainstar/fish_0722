// 主要JavaScript功能

// 文件上傳預覽功能
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            
            // 清除範例圖片選擇狀態
            resetSampleImageButton();
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// 重置範例圖片按鈕狀態
function resetSampleImageButton() {
    const useSampleBtn = document.getElementById('useSampleBtn');
    const sampleInput = document.getElementById('use_sample');
    
    if (useSampleBtn) {
        useSampleBtn.innerHTML = '<i class="fas fa-image"></i><br>' + t('use_sample_image');
        useSampleBtn.classList.remove('btn-success');
        useSampleBtn.classList.add('btn-outline-secondary');
        useSampleBtn.onclick = function() { useSampleImage(); };
    }
    
    if (sampleInput) {
        sampleInput.remove();
    }
}

// 拖拽上傳功能
function setupDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('file');
    
    if (!uploadArea || !fileInput) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadArea.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        fileInput.files = files;
        previewImage(fileInput);
    }
}

// 信心度滑桿更新
function updateConfidenceValue(value) {
    const display = document.getElementById('confidenceValue');
    if (display) {
        display.textContent = parseFloat(value).toFixed(1);
    }
}

// 表單提交處理
function handleFormSubmit() {
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('file');
        const useSampleInput = document.getElementById('use_sample');
        
        // 檢查是否有選擇檔案或使用範例圖片
        if ((!fileInput.files || fileInput.files.length === 0) && !useSampleInput) {
            showAlert(t('please_select_image_or_sample'), 'warning');
            return;
        }
        
        // 如果有選擇檔案，檢查檔案大小
        if (fileInput.files && fileInput.files.length > 0) {
            const maxSize = 16 * 1024 * 1024;
            if (fileInput.files[0].size > maxSize) {
                showAlert(t('file_too_large'), 'danger');
                return;
            }
        }
        
        // 顯示加載狀態
        if (spinner) spinner.style.display = 'block';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner-border text-white" role="status" aria-hidden="true" style="width: 1.5rem; height: 1.5rem;"></span> `;
        }
        
        // 使用 AJAX 提交表單
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect_url) {
                // 成功時跳轉到結果頁面
                window.location.href = data.redirect_url;
            } else {
                // 處理錯誤情況
                showAlert(data.error || t('processing_failed'), 'danger');
                resetSubmitButton();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert(t('network_error'), 'danger');
            resetSubmitButton();
        });
    });
    
    // 重置提交按鈕狀態的輔助函數
    function resetSubmitButton() {
        if (spinner) spinner.style.display = 'none';
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-search"></i> ' + t('start_detection');
        }
    }
}

// 顯示警告訊息
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // 自動隱藏警告
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// 圖片點擊放大功能
function setupImageModal() {
    const images = document.querySelectorAll('.img-fluid');
    
    images.forEach(img => {
        img.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${t('image_preview')}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${this.src}" class="img-fluid" alt="放大圖片">
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            modal.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modal);
            });
        });
    });
}

// 數字計數動畫
function animateNumber(element, start, end, duration) {
    if (!element) return;
    
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// 結果頁面動畫
function setupResultAnimations() {
    const fishCountElement = document.querySelector('.stats-number');
    if (fishCountElement) {
        const finalCount = parseInt(fishCountElement.textContent);
        animateNumber(fishCountElement, 0, finalCount, 1500);
    }
}

// 工具提示初始化
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 複製到剪貼簿功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert(t('copied_to_clipboard'), 'success');
    }, function(err) {
        showAlert(t('copy_failed'), 'danger');
    });
}

// 檔案大小格式化
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 使用範例圖片功能
function useSampleImage() {
    const fileInput = document.getElementById('file');
    const useSampleBtn = document.getElementById('useSampleBtn');
    
    // 創建一個隱藏的 input 來標記使用範例圖片
    let sampleInput = document.getElementById('use_sample');
    if (!sampleInput) {
        sampleInput = document.createElement('input');
        sampleInput.type = 'hidden';
        sampleInput.id = 'use_sample';
        sampleInput.name = 'use_sample';
        document.getElementById('uploadForm').appendChild(sampleInput);
    }
    
    // 設置使用範例圖片
    sampleInput.value = 'A.JPG';
    fileInput.removeAttribute('required');
    
    // 更新按鈕樣式
    useSampleBtn.innerHTML = '<i class="fas fa-check"></i><br>' + t('sample_image_selected');
    useSampleBtn.classList.remove('btn-outline-secondary');
    useSampleBtn.classList.add('btn-success');
    
    // 清除檔案輸入
    fileInput.value = '';
    
    // 清除圖片預覽
    const preview = document.getElementById('imagePreview');
    if (preview) {
        preview.style.display = 'none';
    }
    
    // 清除檔案資訊
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.innerHTML = '<small class="text-success">' + t('sample_image_chosen') + '</small>';
    }
    
    // 新增重置功能
    useSampleBtn.onclick = function() {
        resetImageSelection();
    };
}

// 重置圖片選擇
function resetImageSelection() {
    const fileInput = document.getElementById('file');
    const useSampleBtn = document.getElementById('useSampleBtn');
    const sampleInput = document.getElementById('use_sample');
    
    // 重置檔案輸入
    fileInput.value = '';
    fileInput.setAttribute('required', 'required');
    
    // 移除範例圖片標記
    if (sampleInput) {
        sampleInput.remove();
    }
    
    // 重置按鈕樣式
    useSampleBtn.innerHTML = '<i class="fas fa-image"></i><br>' + t('use_sample_image');
    useSampleBtn.classList.remove('btn-success');
    useSampleBtn.classList.add('btn-outline-secondary');
    
    // 清除圖片預覽
    const preview = document.getElementById('imagePreview');
    if (preview) {
        preview.style.display = 'none';
    }
    
    // 清除檔案資訊
    const fileInfo = document.getElementById('fileInfo');
    if (fileInfo) {
        fileInfo.innerHTML = '';
    }
    
    // 恢復原始功能
    useSampleBtn.onclick = function() {
        useSampleImage();
    };
}

// 頁面加載完成後執行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    setupDragDrop();
    handleFormSubmit();
    setupImageModal();
    setupResultAnimations();
    initTooltips();
    
    // 檔案輸入變化監聽
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            previewImage(this);
            
            // 顯示檔案資訊
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileInfo = document.getElementById('fileInfo');
                if (fileInfo) {
                    fileInfo.innerHTML = `
                        <small class="text-muted">
                            ${t('file_name')}: ${file.name}<br>
                        </small>
                    `;
                }
            }
        });
    }
    
    // 平滑滾動
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// 鍵盤快捷鍵
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + U 快速上傳
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.click();
        }
    }
    
    // ESC 關閉模態框
    if (e.key === 'Escape') {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
});
