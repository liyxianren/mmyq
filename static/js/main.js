// 全局JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    
    // 自动关闭警告信息
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000); // 5秒后自动关闭
    });

    // 表单验证增强
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // 文件上传预览
    const fileInput = document.getElementById('venue_screenshot');
    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                // 检查文件大小
                if (file.size > 16 * 1024 * 1024) { // 16MB
                    alert('文件大小不能超过16MB');
                    this.value = '';
                    return;
                }

                // 检查文件类型
                const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif'];
                if (!allowedTypes.includes(file.type)) {
                    alert('只支持PNG、JPG、JPEG、GIF格式的图片');
                    this.value = '';
                    return;
                }

                // 创建预览
                const reader = new FileReader();
                reader.onload = function(e) {
                    let preview = document.getElementById('imagePreview');
                    if (!preview) {
                        preview = document.createElement('div');
                        preview.id = 'imagePreview';
                        preview.className = 'mt-3';
                        fileInput.parentNode.appendChild(preview);
                    }
                    preview.innerHTML = `
                        <div class="card" style="max-width: 300px;">
                            <img src="${e.target.result}" class="card-img-top" alt="预览图" style="height: 200px; object-fit: cover;">
                            <div class="card-body p-2">
                                <small class="text-muted">预览：${file.name}</small>
                            </div>
                        </div>
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 确认对话框增强
    const confirmLinks = document.querySelectorAll('a[onclick*="confirm"]');
    confirmLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            const confirmText = this.getAttribute('onclick').match(/confirm\('(.+?)'\)/)[1];
            if (!confirm(confirmText)) {
                event.preventDefault();
            }
        });
    });

    // 数据表格排序功能
    const sortableHeaders = document.querySelectorAll('.table th[data-sort]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' ↕️';
        
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const column = Array.from(this.parentNode.children).indexOf(this);
            const isAsc = this.classList.contains('sort-asc');
            
            // 重置所有排序图标
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            
            // 排序数据
            rows.sort((a, b) => {
                const aText = a.cells[column].textContent.trim();
                const bText = b.cells[column].textContent.trim();
                return isAsc ? bText.localeCompare(aText) : aText.localeCompare(bText);
            });
            
            // 更新表格
            rows.forEach(row => tbody.appendChild(row));
            
            // 更新排序状态
            this.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
        });
    });

    // 搜索功能
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // 时间格式化
    const timeElements = document.querySelectorAll('[data-time]');
    timeElements.forEach(element => {
        const time = new Date(element.getAttribute('data-time'));
        element.textContent = time.toLocaleString('zh-CN');
    });

    // 工具提示初始化
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 返回顶部按钮
    const backToTopButton = createBackToTopButton();
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
});

// 创建返回顶部按钮
function createBackToTopButton() {
    const button = document.createElement('button');
    button.innerHTML = '↑';
    button.className = 'btn btn-primary rounded-circle position-fixed';
    button.style.cssText = `
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        z-index: 1000;
        display: none;
        font-size: 20px;
    `;
    
    button.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    document.body.appendChild(button);
    return button;
}

// 通用工具函数
const Utils = {
    // 格式化文件大小
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 显示加载状态
    showLoading: function(element) {
        const originalText = element.textContent;
        element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>加载中...';
        element.disabled = true;
        return originalText;
    },
    
    // 隐藏加载状态
    hideLoading: function(element, originalText) {
        element.textContent = originalText;
        element.disabled = false;
    },
    
    // 复制到剪贴板
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(function() {
            // 显示成功提示
            const toast = document.createElement('div');
            toast.className = 'position-fixed top-0 end-0 p-3';
            toast.style.zIndex = '1060';
            toast.innerHTML = `
                <div class="toast show" role="alert">
                    <div class="toast-body">
                        复制成功！
                    </div>
                </div>
            `;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 3000);
        });
    }
};