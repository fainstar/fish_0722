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
            
            modal.addEventListener('hidden.bs.modal', function() {
                modal.remove();
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    // Call initialization functions
    setupDragDrop();
    handleFormSubmit();
    setupImageModal();

    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const sampleInput = document.getElementById('use_sample');
                if (sampleInput) {
                    resetImageSelection();
                }
            }
        });
    }
});

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
    useSampleBtn.innerHTML = '<i class="fas fa-check"></i> Sample Image Selected';
    useSampleBtn.classList.remove('btn-outline-secondary');
    useSampleBtn.classList.add('btn-success', 'btn-sm');
    
    // 清除檔案輸入
    fileInput.value = '';
    
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
    
    // 重置範例圖片設定
    if (sampleInput) {
        sampleInput.remove();
    }
    
    // 重置按鈕
    useSampleBtn.innerHTML = '<i class="fas fa-image"></i> Use Sample Image';
    useSampleBtn.classList.remove('btn-success');
    useSampleBtn.classList.add('btn-outline-secondary', 'btn-sm');
    useSampleBtn.onclick = function() {
        useSampleImage();
    };
    
    // 不需要重新設定 required，因為現在是可選的
}
