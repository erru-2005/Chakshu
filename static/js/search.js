// Advanced real-time search functionality with animations
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const studentList = document.getElementById('studentList');
    
    if (searchInput) {
        // Store original content
        const originalContent = studentList.innerHTML;
        studentList.setAttribute('data-original-content', originalContent);
        
        // Add debounce to avoid excessive API calls
        let searchTimeout = null;
        
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            
            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Add loading state
            studentList.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';
            
            // Set new timeout
            searchTimeout = setTimeout(() => {
                if (query.length === 0) {
                    showAllStudents();
                    return;
                }
                
                performSearch(query);
                }, 300);
        });
    }
});

function performSearch(query) {
    const startTime = performance.now();
    
    // Make API request
    fetch('/search_students', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            filter: 'all'
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const endTime = performance.now();
        const searchTime = ((endTime - startTime) / 1000).toFixed(2);
        
        // Update search stats
        document.getElementById('searchResultsCount').textContent = `${data.students.length} results`;
        document.getElementById('searchTime').textContent = `in ${searchTime}s`;
        
        if (data.students.length === 0) {
            studentList.innerHTML = `
                <div class="no-results text-center py-5">
                    <i class="fas fa-search fa-3x mb-3 text-muted"></i>
                    <h4 class="text-muted">No results found</h4>
                    <p class="text-muted">Try different search terms</p>
                </div>
            `;
        return;
        }
        
        // Group students by class
        const studentsByClass = {};
        data.students.forEach(student => {
            const className = student.classSection || 'Unassigned';
            if (!studentsByClass[className]) {
                studentsByClass[className] = [];
            }
            studentsByClass[className].push(student);
        });
        
        // Build the HTML for the results
        let html = '';
        for (const [className, classStudents] of Object.entries(studentsByClass)) {
            html += `
                <div class="category-section">
                    <div class="category-header">
                        <div class="category-title">
                            <i class="fas fa-graduation-cap"></i>
                            ${className}
                        </div>
                        <div class="category-actions">
                            <div class="category-count">
                                ${classStudents.length} Students
                            </div>
                        </div>
                    </div>
                    <div class="student-grid">
            `;
            
            classStudents.forEach(student => {
        html += `
                    <div class="student-card">
                        <div class="student-card-header">
                <div class="student-info">
                                <div class="student-name">${student.studentName}</div>
                                <div class="student-details">
                                    <div class="detail-line">
                                        <i class="fas fa-id-card"></i>
                                        <span>${student.rollNo}</span>
                                    </div>
                                    <div class="detail-line">
                                        <i class="fas fa-registered"></i>
                                        <span>${student.regNo || 'N/A'}</span>
                                    </div>
                                </div>
                            </div>
                </div>
                        <div class="student-card-actions">
                            <button class="btn btn-primary btn-sm" 
                                    data-student='${JSON.stringify(student)}'
                                    onclick="viewStudentDetails(this)">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-warning btn-sm" 
                                    onclick="editStudent('${student.rollNo}')">
                        <i class="fas fa-edit"></i>
                    </button>
                            <button class="btn btn-danger btn-sm" 
                                    data-student-id="${student.rollNo}"
                                    data-student-name="${student.studentName}"
                                    data-student-class="${student.classSection || 'Unassigned'}"
                                    onclick="deleteStudentFromSearch(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        studentList.innerHTML = html;
    })
    .catch(error => {
        console.error('Search error:', error);
        studentList.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                An error occurred while searching. Please try again.
            </div>
        `;
    });
}

function showAllStudents() {
    const studentList = document.getElementById('studentList');
    const originalContent = studentList.getAttribute('data-original-content');
    if (originalContent) {
        studentList.innerHTML = originalContent;
    }
    
    // Update search stats
    document.getElementById('searchResultsCount').textContent = '0 results';
    document.getElementById('searchTime').textContent = '';
}

// Function to view student details
function viewStudentDetails(button) {
    const studentData = JSON.parse(button.getAttribute('data-student'));
    console.log('Student Data:', studentData); // Debug log
    
    const modal = new bootstrap.Modal(document.getElementById('studentDetailsModal'));
    const modalBody = document.getElementById('studentDetails');
    
    // Build the student details HTML with a modern, attractive layout
    modalBody.innerHTML = `
        <div class="student-profile">
            <div class="profile-header">
                <div class="avatar-circle">
                    ${studentData.studentName.charAt(0).toUpperCase()}
                </div>
                <div class="header-info">
                    <h2 class="student-name">${studentData.studentName}</h2>
                    <div class="student-badges">
                        <span class="badge bg-primary">
                            <i class="fas fa-id-card"></i>
                            ${studentData.rollNo}
                        </span>
                        <span class="badge bg-info">
                            <i class="fas fa-graduation-cap"></i>
                            ${studentData.classSection || 'Unassigned'}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Tab Navigation -->
            <div class="nav-tabs">
                <button class="nav-link active" data-tab="#basicInfo">
                    <i class="fas fa-user"></i>
                    Basic Info
                </button>
                <button class="nav-link" data-tab="#contactInfo">
                    <i class="fas fa-address-book"></i>
                    Contact Info
                </button>
                <button class="nav-link" data-tab="#academicInfo">
                    <i class="fas fa-graduation-cap"></i>
                    Academic Info
                </button>
                <button class="nav-link" data-tab="#additionalInfo">
                    <i class="fas fa-info-circle"></i>
                    Additional Info
                </button>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
                <!-- Basic Information Tab -->
                <div id="basicInfo" class="tab-pane active">
                    <div class="detail-section">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Registration Number</span>
                                <span class="detail-value">${studentData.regNo || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Father's Name</span>
                                <span class="detail-value">${studentData.fatherName || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Gender</span>
                                <span class="detail-value">${studentData.gender || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Date of Birth</span>
                                <span class="detail-value">${studentData.dob || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Religion</span>
                                <span class="detail-value">${studentData.religion || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Caste</span>
                                <span class="detail-value">${studentData.caste || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Contact Information Tab -->
                <div id="contactInfo" class="tab-pane">
                    <div class="detail-section">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Email</span>
                                <span class="detail-value">${studentData.email || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Student Contact</span>
                                <span class="detail-value">${studentData.studentContact || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Parent's Contact</span>
                                <span class="detail-value">${studentData.parentNo || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Address</span>
                                <span class="detail-value">${studentData.address || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">State</span>
                                <span class="detail-value">${studentData.state || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">District</span>
                                <span class="detail-value">${studentData.district || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Academic Information Tab -->
                <div id="academicInfo" class="tab-pane">
                    <div class="detail-section">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Program Name</span>
                                <span class="detail-value">${studentData.programName || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Discipline</span>
                                <span class="detail-value">${studentData.discipline1 || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Language</span>
                                <span class="detail-value">${studentData.lang2 || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Roll No</span>
                                <span class="detail-value">${studentData.pucRollNo || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Year</span>
                                <span class="detail-value">${studentData.pucYear || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Institute</span>
                                <span class="detail-value">${studentData.pucInstitute || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Total Marks</span>
                                <span class="detail-value">${studentData.pucTotalMarks || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Obtained Marks</span>
                                <span class="detail-value">${studentData.pucObtainedMarks || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">PUC Percentage</span>
                                <span class="detail-value">${studentData.pucPercentage || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Additional Information Tab -->
                <div id="additionalInfo" class="tab-pane">
                    <div class="detail-section">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Aadhar Number</span>
                                <span class="detail-value">${studentData.aadharNo || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Blood Group</span>
                                <span class="detail-value">${studentData.bloodGroup || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Category</span>
                                <span class="detail-value">${studentData.category || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Category Applied</span>
                                <span class="detail-value">${studentData.categoryApplied || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Income</span>
                                <span class="detail-value">${studentData.income || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">ABC ID</span>
                                <span class="detail-value">${studentData.abcId || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add tab switching functionality
    const tabButtons = modalBody.querySelectorAll('.nav-link');
    const tabPanes = modalBody.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button
            this.classList.add('active');

            // Show corresponding tab pane
            const targetPane = modalBody.querySelector(this.getAttribute('data-tab'));
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
    
    modal.show();
}

// Function to edit student
function editStudent(studentId) {
    window.location.href = `/edit_student/${studentId}`;
}

// Function to delete student from search results
function deleteStudentFromSearch(button) {
    const studentId = button.getAttribute('data-student-id');
    const studentName = button.getAttribute('data-student-name');
    const studentClass = button.getAttribute('data-student-class');
    
    // Show confirmation dialog
    if (confirm(`Are you sure you want to delete the student "${studentName}" from the search results?`)) {
        // Make AJAX request to delete student
        fetch(`/delete_student/${studentId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                // Remove student from search results
                const studentCard = button.closest('.student-card');
                const categorySection = studentCard.closest('.category-section');
                studentCard.remove();
                
                // Update student count
                const countElement = categorySection.querySelector('.category-count');
                const currentCount = parseInt(countElement.textContent);
                countElement.textContent = `${currentCount - 1} Students`;
                
                // If no students left in the category, remove the category section
                if (currentCount - 1 === 0) {
                    categorySection.remove();
                }
                
                // Show success message
                showNotification('Student deleted successfully!', 'success');
            } else {
                showNotification('Error deleting student', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting student:', error);
            showNotification('Error deleting student', 'error');
        });
    }
} 