document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner'); // Corrected from loadingDiv to spinner

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Show loading spinner
            if (spinner) spinner.style.display = 'block';
            if (submitBtn) {
                submitBtn.disabled = true;
                const processingText = spinner ? spinner.querySelector('p').textContent : 'Processing...';
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${processingText}`;
            }

            const formData = new FormData(uploadForm);

            fetch(uploadForm.action, {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (!response.ok) {
                    // If response is not ok, try to parse error from JSON body
                    return response.json().then(err => { 
                        // Create a new error with the message from server
                        throw new Error(err.error || 'An unknown error occurred.'); 
                    });
                }
                // If response is ok, it means success and we will be redirected.
                // The server should send a JSON response with a redirect URL.
                return response.json();
            })
            .then(data => {
                if (data.redirect_url) {
                    // Redirect to the result page
                    window.location.href = data.redirect_url;
                } else {
                    // Handle cases where redirect_url is not provided, though it shouldn't happen on success
                    throw new Error('Response did not contain a redirect URL.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (spinner) spinner.style.display = 'none';
                
                // Display error in a more user-friendly way, e.g., using the alert container
                const alertContainer = document.getElementById('alert-container');
                if (alertContainer) {
                    const alertEl = document.createElement('div');
                    alertEl.className = 'alert alert-danger alert-dismissible fade show';
                    alertEl.setAttribute('role', 'alert');
                    alertEl.innerHTML = `
                        ${error.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    alertContainer.appendChild(alertEl);
                } else {
                    // Fallback to default alert if container is not found
                    alert(`An error occurred: ${error.message}`);
                }
            })
            .finally(() => {
                // Re-enable submit button in case of error, as success will navigate away
                if (submitBtn) {
                    submitBtn.disabled = false;
                    // This text should be translated or fetched from a data attribute
                    submitBtn.innerHTML = `<i class="fas fa-search"></i> Start Detection`; 
                }
            });
        });
    }
});

function updateConfidenceValue(val) {
    const confidenceValueEl = document.getElementById('confidenceValue');
    if (confidenceValueEl) {
        confidenceValueEl.textContent = val;
    }
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

// 當使用者選擇檔案時，重置範例圖片選擇
document.addEventListener('DOMContentLoaded', function() {
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
