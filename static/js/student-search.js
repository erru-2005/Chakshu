// Enhanced Student Search & Template Functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchAnimation = document.querySelector('.search-animation');
    const studentRows = document.querySelectorAll('.student-row');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const templateButton = document.querySelector('.btn-template');
    const rows = studentRows || [];

    let searchTimeout;
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.toLowerCase().trim();
            
            // Show loading animation
            searchAnimation.style.opacity = '1';
            this.classList.add('searching');
            
            searchTimeout = setTimeout(() => {
                let hasResults = false;
                
                rows.forEach(row => {
                    const studentData = row.getAttribute('data-student').toLowerCase();
                    const matches = studentData.includes(query);
                    
                    if (matches) {
                        row.style.display = '';
                        row.classList.add('filtered-in');
                        setTimeout(() => row.classList.remove('filtered-in'), 500);
                        hasResults = true;
                    } else {
                        row.style.display = 'none';
                    }
                });
                
                // Handle no results message
                if (noResultsMessage) {
                    if (!hasResults && query) {
                        noResultsMessage.style.display = 'block';
                        noResultsMessage.style.animation = 'fadeIn 0.3s ease';
                    } else {
                        noResultsMessage.style.display = 'none';
                    }
                }
                
                // Hide loading animation
                searchAnimation.style.opacity = '0';
                this.classList.remove('searching');
            }, 300);
        });
    }

    // Template download functionality
    if (templateButton) {
        templateButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add loading state
            this.classList.add('loading');
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Downloading...</span>';
            
            fetch(this.href)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'student_template.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // Show success animation
                    this.innerHTML = '<i class="fas fa-check"></i><span>Downloaded!</span>';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-file-excel"></i><span>Download Template</span>';
                        this.classList.remove('loading');
                    }, 1500);
                })
                .catch(error => {
                    console.error('Download failed:', error);
                    this.innerHTML = '<i class="fas fa-exclamation-circle"></i><span>Download Failed</span>';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-file-excel"></i><span>Download Template</span>';
                        this.classList.remove('loading');
                    }, 1500);
                });
        });
    }

    // Excel file validation
    const excelUploadInput = document.getElementById('excelUpload');
    if (excelUploadInput) {
        excelUploadInput.addEventListener('change', function() {
            const file = this.files[0];
            const uploadBtn = document.querySelector('.btn-excel-upload');
            
            if (file) {
                const fileExt = file.name.split('.').pop().toLowerCase();
                
                // Validate file extension
                if (fileExt === 'xlsx' || fileExt === 'xls') {
                    uploadBtn.removeAttribute('disabled');
                    uploadBtn.classList.add('btn-success');
                    showMessage('File ready for upload!', 'success');
                } else {
                    this.value = ''; // Clear the input
                    uploadBtn.setAttribute('disabled', 'true');
                    uploadBtn.classList.remove('btn-success');
                    showMessage('Please upload only Excel files (.xlsx, .xls)', 'error');
                }
            }
        });
    }
    
    // Helper function for showing messages
    function showMessage(text, type) {
        // Check if message container exists, create if not
        let messageContainer = document.getElementById('messageContainer');
        if (!messageContainer) {
            messageContainer = document.createElement('div');
            messageContainer.id = 'messageContainer';
            messageContainer.style.position = 'fixed';
            messageContainer.style.top = '20px';
            messageContainer.style.right = '20px';
            messageContainer.style.zIndex = '9999';
            document.body.appendChild(messageContainer);
        }
        
        const message = document.createElement('div');
        message.className = `alert alert-${type === 'error' ? 'danger' : 'success'} fade show`;
        message.innerHTML = `
            ${text}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        
        messageContainer.appendChild(message);
        
        // Auto-close after 4 seconds
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 4000);
    }
});

// Add styles for loading state
const style = document.createElement('style');
style.textContent = `
    .btn-template.loading {
        opacity: 0.8;
        pointer-events: none;
    }
    
    .btn-template i.fa-spinner {
        animation: spin 1s linear infinite;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style); 