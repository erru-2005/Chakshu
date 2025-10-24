// Excel file upload handler with validation
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const uploadForm = document.getElementById('uploadForm');
    
    if (!uploadArea || !fileInput) return;
    
    // Handle drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('highlight');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('highlight');
    }
    
    // Handle file drop
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            fileInput.files = files;
            handleFiles(files);
        }
    }
    
    // Handle file selection via input - only trigger on explicit user interaction
    fileInput.addEventListener('click', function(e) {
        e.stopPropagation(); // Prevent event bubbling
    });
    
    fileInput.addEventListener('change', function(e) {
        e.stopPropagation(); // Prevent event bubbling
        if (fileInput.files.length) {
            handleFiles(fileInput.files);
        }
    });
    
    // Add click handler to upload area to trigger file input
    uploadArea.addEventListener('click', function(e) {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });
    
    function handleFiles(files) {
        const file = files[0];
        
        // Check file type
        const validTypes = ['.xlsx', '.xls'];
        const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            showError('Please upload only Excel files (.xlsx or .xls)', true);
            fileInput.value = ''; // Clear the file input
            return;
        }
        
        // Check file size (16MB max)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            showError('File size exceeds the maximum limit of 16MB', true);
            fileInput.value = ''; // Clear the file input
            return;
        }
        
        // Show progress
        uploadPreview.style.display = 'none';
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        
        // Create FormData and upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('importNow', 'false'); // Default to preview first
        
        // Simulate progress for better UX
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            progressBar.style.width = `${Math.min(progress, 90)}%`;
            
            if (progress >= 90) {
                clearInterval(progressInterval);
            }
        }, 100);
        
        // Upload the file
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            progressBar.style.width = '100%';
            return response.json();
        })
        .then(data => {
            // Hide progress after a moment
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                
                if (data.success) {
                    // Show preview and actions
                    displayPreview(data);
                    uploadPreview.style.display = 'block';
                } else {
                    // Show error and clear form
                    showError(data.message || 'Error uploading file', true);
                    uploadForm.reset();
                    
                    // Close upload container if validation fails
                    const uploadContainer = document.querySelector('.upload-container');
                    if (uploadContainer && data.message && 
                        (data.message.includes('Missing required columns') || 
                         data.message.includes('Empty roll numbers'))) {
                        setTimeout(() => {
                            uploadContainer.style.display = 'none';
                        }, 3000);
                    }
                }
            }, 500);
        })
        .catch(error => {
            clearInterval(progressInterval);
            uploadProgress.style.display = 'none';
            showError('Error uploading file: ' + error.message, true);
        });
    }
    
    function displayPreview(data) {
        if (!data.preview || !data.preview.length) {
            uploadPreview.innerHTML = '<div class="alert alert-info">No preview data available</div>';
            return;
        }
        
        // Build table for preview
        let html = `
            <h4>File Preview (showing first ${data.preview.length} rows)</h4>
            <div class="table-responsive">
                <table class="table table-sm table-striped">
                    <thead class="thead-light">
                        <tr>
        `;
        
        // Get all columns from first record
        const columns = Object.keys(data.preview[0]);
        
        // Add headers
        columns.forEach(column => {
            html += `<th>${column}</th>`;
        });
        
        html += `
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add rows
        data.preview.forEach(row => {
            html += '<tr>';
            columns.forEach(column => {
                html += `<td>${row[column] !== undefined && row[column] !== null ? row[column] : ''}</td>`;
            });
            html += '</tr>';
        });
        
        html += `
                    </tbody>
                </table>
            </div>
            <div class="upload-actions">
                <button type="button" class="btn btn-secondary" id="cancelUpload">Cancel</button>
                <button type="button" class="btn btn-primary" id="confirmUpload">Import Data</button>
            </div>
        `;
        
        uploadPreview.innerHTML = html;
        
        // Add event handlers for buttons
        document.getElementById('cancelUpload').addEventListener('click', function() {
            uploadPreview.style.display = 'none';
            uploadForm.reset();
        });
        
        document.getElementById('confirmUpload').addEventListener('click', function() {
            importExcel(data.file_path);
        });
    }
    
    function importExcel(filePath) {
        // Show progress again
        uploadPreview.style.display = 'none';
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        
        // Create FormData for import
        const formData = new FormData();
        formData.append('file_path', filePath);
        formData.append('importNow', 'true');
        
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 3;
            progressBar.style.width = `${Math.min(progress, 90)}%`;
            
            if (progress >= 90) {
                clearInterval(progressInterval);
            }
        }, 100);
        
        // Make the import request
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            clearInterval(progressInterval);
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            progressBar.style.width = '100%';
            return response.json();
        })
        .then(data => {
            setTimeout(() => {
                uploadProgress.style.display = 'none';
                uploadForm.reset();
                
                if (data.success) {
                    // Show success message with animation
                    showSuccess(`${data.details.success} students imported successfully!`, true);
                    
                    // Refresh student list if on management page
                    if (typeof refreshStudentList === 'function') {
                        refreshStudentList();
                    }
                    
                    // Hide upload container after successful import
                    const uploadContainer = document.querySelector('.upload-container');
                    if (uploadContainer) {
                        setTimeout(() => {
                            uploadContainer.style.display = 'none';
                        }, 3000);
                    }
                } else {
                    showError(data.message || 'Error importing data', true);
                }
            }, 500);
        })
        .catch(error => {
            clearInterval(progressInterval);
            uploadProgress.style.display = 'none';
            showError('Error importing data: ' + error.message, true);
        });
    }
}); 