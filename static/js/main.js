// اسکریپت‌های عمومی سیستم

// فعال کردن tooltip‌های Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// مدیریت فرم‌ها
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// نمایش تأییدیه قبل از حذف
function confirmDelete(message = 'آیا از حذف این آیتم مطمئن هستید؟') {
    return confirm(message);
}

// مدیریت آپدیت خودکار داده‌ها
function autoRefreshData(containerId, url, interval = 30000) {
    setInterval(() => {
        fetch(url)
            .then(response => response.json())
            .then(data => {
                updateContainer(containerId, data);
            })
            .catch(error => console.error('Error refreshing data:', error));
    }, interval);
}

function updateContainer(containerId, data) {
    // این تابع باید بر اساس ساختار داده‌ها کاستومایز شود
    console.log('Updating container:', containerId, data);
}

// مدیریت نمایش تاریخ شمسی
function getCurrentShamsiDate() {
    const now = new Date();
    // اینجا می‌توانید از کتابخانه‌ی تاریخ شمسی استفاده کنید
    return now.toLocaleDateString('fa-IR');
}

// مدیریت ارسال فرم با AJAX
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            successCallback(data);
        } else {
            errorCallback(data);
        }
    })
    .catch(error => {
        errorCallback(error);
    });
}

// مدیریت نمایش نوتیفیکیشن
function showNotification(message, type = 'success') {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const iconClass = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // اضافه کردن نوتیفیکیشن به ابتدای container
    const container = document.querySelector('.container');
    container.insertBefore(notification, container.firstChild);
    
    // حذف خودکار پس از 5 ثانیه
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// مدیریت جستجو در جداول
function setupTableSearch(tableId, searchInputId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) return;
    
    searchInput.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const cells = rows[i].getElementsByTagName('td');
            let found = false;
            
            for (let j = 0; j < cells.length; j++) {
                const cellText = cells[j].textContent || cells[j].innerText;
                if (cellText.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
            
            rows[i].style.display = found ? '' : 'none';
        }
    });
}

// مدیریت مرتب‌سازی جداول
function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    const isNumeric = !isNaN(parseFloat(rows[0].cells[columnIndex].textContent));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            return parseFloat(aValue) - parseFloat(bValue);
        } else {
            return aValue.localeCompare(bValue, 'fa');
        }
    });
    
    // حذف ردیف‌های فعلی
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    // اضافه کردن ردیف‌های مرتب‌شده
    rows.forEach(row => tbody.appendChild(row));
}

// مدیریت چاپ گزارش
function printReport(elementId) {
    const printContent = document.getElementById(elementId).innerHTML;
    const originalContent = document.body.innerHTML;
    
    document.body.innerHTML = printContent;
    window.print();
    document.body.innerHTML = originalContent;
    location.reload();
}

// مدیریت اکسپورت داده‌ها
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            row.push(cols[j].innerText);
        }
        
        csv.push(row.join(','));
    }
    
    // دانلود فایل
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// مدیریت بارگذاری تصاویر و فایل‌ها
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onloadend = function() {
        preview.src = reader.result;
    };
    
    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = '';
    }
}