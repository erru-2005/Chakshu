from flask import Flask, render_template, request, jsonify, url_for, flash, redirect, send_file
import os
from dotenv import load_dotenv
import json
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import PatternFill, Border, Side

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Add secret key for flash messages
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_development')

# Configure upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# JSON storage file path
STUDENTS_JSON = 'students.json'

def load_students():
    if os.path.exists(STUDENTS_JSON):
        with open(STUDENTS_JSON, 'r') as f:
            return json.load(f)
    return []

def save_students(students):
    with open(STUDENTS_JSON, 'w') as f:
        json.dump(students, f, indent=4)

@app.route('/')
def index():
    return render_template('student_form.html')

@app.route('/search_barcode', methods=['POST'])
def search_barcode():
    try:
        data = request.json
        barcode = data.get('barcode')
        
        if not barcode:
            return jsonify({'error': 'Barcode is required'}), 400

        students = load_students()
        student = next((s for s in students if s.get('rollNo') == barcode), None)
        
        if student:
            return jsonify(student), 200
        else:
            return jsonify({'error': f'No student found with Roll Number: {barcode}'}), 404

    except Exception as e:
        print(f"Error in search_barcode: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    try:
        data = request.json
        roll_no = data.get('rollNo')
        reg_no = data.get('regNo')
        
        if not roll_no:
            return jsonify({'error': 'Roll number is required'}), 400

        students = load_students()
        
        # Check for duplicate roll number
        if any(s.get('rollNo') == roll_no for s in students):
            return jsonify({
                'isDuplicate': True,
                'message': f'Student with Roll Number {roll_no} already exists!'
            }), 200

        # Check for duplicate registration number if provided
        if reg_no and any(s.get('regNo') == reg_no for s in students):
            return jsonify({
                'isDuplicate': True,
                'message': f'Student with Registration Number {reg_no} already exists!'
            }), 200

        return jsonify({'isDuplicate': False}), 200

    except Exception as e:
        print(f"Error in check_duplicate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Check content type to handle both form data and JSON requests
        student_data = {}
        if request.content_type and 'application/json' in request.content_type:
            # JSON request
            data = request.json
            for key, value in data.items():
                student_data[key] = value
        else:
            # Form data request
            for key in request.form:
                student_data[key] = request.form.get(key)
        
        print("Received student data:", student_data)  # Debug print
        
        # Handle profile image upload
        if 'profileImage' in request.files:
            profile_image = request.files['profileImage']
            if profile_image and profile_image.filename:
                # Only process if roll number is provided
                if 'rollNo' in student_data and student_data['rollNo']:
                    # Get file extension
                    filename = secure_filename(profile_image.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                    
                    # Create new filename using roll number
                    new_filename = f"{student_data['rollNo']}.{file_ext}"
                    
                    # Ensure upload directory exists
                    upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)
                    
                    # Save file
                    file_path = os.path.join(upload_path, new_filename)
                    profile_image.save(file_path)
                    print(f"Saved profile image to {file_path}")
                    
                    # Store the relative path in student data
                    student_data['profileImage'] = f"uploads/{new_filename}"
                    print(f"Set profile image path to: {student_data['profileImage']}")
        
        # Remove None and empty string values
        student_data = {k: v for k, v in student_data.items() if v is not None and v != ''}
        
        print("Processed student data:", student_data)  # Debug print

        # Validate required fields
        if not student_data.get('rollNo'):
            return jsonify({'error': 'Roll number is required'}), 400

        try:
            # Check for duplicates before saving
            students = load_students()
            
            # First check if document with this roll number already exists
            if any(s.get('rollNo') == student_data['rollNo'] for s in students):
                return jsonify({
                    'error': f'Student with Roll Number {student_data["rollNo"]} already exists!'
                }), 409

            # Check for duplicate registration number if provided
            if student_data.get('regNo') and any(s.get('regNo') == student_data['regNo'] for s in students):
                return jsonify({
                    'error': f'Student with Registration Number {student_data["regNo"]} already exists!'
                }), 409

            # Add timestamp
            student_data['createdAt'] = datetime.now().isoformat()
            
            # Save to JSON
            students.append(student_data)
            save_students(students)
            print(f"New student data saved for roll number: {student_data['rollNo']}")
            
            return jsonify({
                'success': True,
                'message': 'Student data saved successfully!',
                'studentId': student_data['rollNo']
            }), 200

        except Exception as e:
            print(f"Error saving student data: {str(e)}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500

    except Exception as e:
        print(f"Error in submit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/manage')
def manage_students():
    try:
        print("Starting manage_students route...")
        students = load_students()
        
        # Convert to list of dictionaries and organize by class
        students_list = []
        students_by_class = {}
        
        student_count = 0
        for student in students:
            student_data = student
            student_data['id'] = student_data['rollNo']
            students_list.append(student_data)
            student_count += 1
            
            # Organize students by class
            class_section = student_data.get('classSection', 'Unassigned')
            if class_section not in students_by_class:
                students_by_class[class_section] = []
            students_by_class[class_section].append(student_data)
        
        print(f"Found {student_count} students")
        print(f"Classes found: {list(students_by_class.keys())}")
        
        # Sort students in each class by roll number
        for class_section in students_by_class:
            students_by_class[class_section].sort(key=lambda x: x.get('rollNo', ''))
        
        # Sort the main list by roll number
        students_list.sort(key=lambda x: x.get('rollNo', ''))
        
        print("Rendering template with data...")
        return render_template('student_management.html', 
                            students=students_list,
                            students_by_class=students_by_class,
                            has_students=student_count > 0)
    except Exception as e:
        print(f"Error in manage_students: {str(e)}")
        # Return empty lists instead of error
        return render_template('student_management.html',
                            students=[],
                            students_by_class={},
                            has_students=False)

@app.route('/search_students', methods=['POST'])
def search_students():
    try:
        data = request.json
        query = data.get('query', '').strip().lower()
        filter_type = data.get('filter', 'all')
        
        if not query:
            return jsonify({'students': []}), 200

        students = load_students()
        filtered_students = []
        
        for student in students:
            # Get student data with default values
            student_name = student.get('studentName', '').lower()
            roll_no = student.get('rollNo', '').lower()
            class_section = student.get('classSection', '').lower()
            
            # Apply search based on filter type
            match_found = False
            
            if filter_type == 'all':
                # Search in all relevant fields
                match_found = (query in student_name or 
                             query in roll_no or 
                             query in class_section)
            elif filter_type == 'name':
                match_found = query in student_name
            elif filter_type == 'roll':
                match_found = query in roll_no
            elif filter_type == 'class':
                match_found = query in class_section
            
            if match_found:
                # Return all student data
                filtered_students.append(student)
        
        # Sort results by roll number
        filtered_students.sort(key=lambda x: x.get('rollNo', ''))
        
        # Limit to 20 results
        filtered_students = filtered_students[:20]
        
        return jsonify({'students': filtered_students}), 200
        
    except Exception as e:
        print(f"Error in search_students: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/advanced_search', methods=['POST'])
def advanced_search():
    try:
        criteria = request.json
        students = load_students()
        filtered_students = []
        
        for student in students:
            match = True
            
            # Name criteria
            if criteria.get('name') and criteria['name'].strip():
                if criteria['name'].lower() not in student.get('studentName', '').lower():
                    match = False
            
            # Roll number criteria
            if criteria.get('rollNo') and criteria['rollNo'].strip():
                if criteria['rollNo'].lower() not in student.get('rollNo', '').lower():
                    match = False
            
            # Class section criteria
            if criteria.get('classSection') and criteria['classSection'].strip():
                if criteria['classSection'].lower() not in student.get('classSection', '').lower():
                    match = False
            
            # Gender criteria
            if criteria.get('gender') and criteria['gender'].strip():
                if criteria['gender'].lower() != student.get('gender', '').lower():
                    match = False
            
            # Blood group criteria
            if criteria.get('bloodGroup') and criteria['bloodGroup'].strip():
                if criteria['bloodGroup'].lower() != student.get('bloodGroup', '').lower():
                    match = False
            
            # Category criteria
            if criteria.get('category') and criteria['category'].strip():
                if criteria['category'].lower() not in student.get('category', '').lower():
                    match = False
            
            # Address criteria
            if criteria.get('address') and criteria['address'].strip():
                if criteria['address'].lower() not in student.get('address', '').lower():
                    match = False
            
            if match:
                # Return all student data
                filtered_students.append(student)
        
        # Sort results by roll number
        filtered_students.sort(key=lambda x: x.get('rollNo', ''))
        
        # Limit to 30 results
        filtered_students = filtered_students[:30]
        
        return jsonify({'students': filtered_students}), 200
        
    except Exception as e:
        print(f"Error in advanced_search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_student_details/<student_id>')
def get_student_details(student_id):
    try:
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == student_id), None)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        return jsonify(student), 200
    except Exception as e:
        print(f"Error in get_student_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    try:
        # For GET requests, display the edit form
        if request.method == 'GET':
            students = load_students()
            student = next((s for s in students if s.get('rollNo') == student_id), None)
            
            if student:
                return render_template('student_update.html', student=student)
            else:
                flash(f'Student with ID {student_id} not found', 'error')
                return redirect(url_for('manage_students'))
                
        # For POST requests, process the form submission
        elif request.method == 'POST':
            # Get data from form
            updated_data = {}
            for key in request.form:
                updated_data[key] = request.form.get(key)
                
            print(f"Edit student form data received for {student_id}: {updated_data}")
            print(f"Files in request: {list(request.files.keys())}")
                
            # Handle profile image upload
            if 'profileImage' in request.files:
                profile_image = request.files['profileImage']
                print(f"Profile image file: {profile_image}, filename: {profile_image.filename}")
                if profile_image and profile_image.filename:
                    # Get file extension
                    filename = secure_filename(profile_image.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
                    
                    # Create new filename using student ID (roll number)
                    new_filename = f"{student_id}.{file_ext}"
                    
                    # Ensure upload directory exists
                    upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)
                    
                    # Save file
                    file_path = os.path.join(upload_path, new_filename)
                    print(f"Saving profile image to: {file_path}")
                    profile_image.save(file_path)
                    print(f"Saved profile image to {file_path}")
                    
                    # Store the relative path in student data
                    updated_data['profileImage'] = f"uploads/{new_filename}"
                    print(f"Set profile image path to: {updated_data['profileImage']}")
                
            # Remove None and empty string values
            updated_data = {k: v for k, v in updated_data.items() if v is not None and v != ''}
            
            # Update the student in the JSON file
            students = load_students()
            
            # Find the student by ID (roll number)
            student_index = next((i for i, s in enumerate(students) if s.get('rollNo') == student_id), None)
            
            if student_index is not None:
                # Update the student data
                students[student_index].update(updated_data)
                
                # Save the updated students list
                save_students(students)
                
                flash('Student data updated successfully!', 'success')
            else:
                flash(f'Student with ID {student_id} not found', 'error')
                
            return redirect(url_for('manage_students'))

    except Exception as e:
        print(f"Error in edit_student: {str(e)}")
        flash(f'Error updating student: {str(e)}', 'error')
        return redirect(url_for('manage_students'))

@app.route('/delete_student/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == student_id), None)
        
        if not student:
            return jsonify({
                'success': False,
                'error': 'Student not found'
            }), 404
            
        # Remove the student from the list
        students = [s for s in students if s.get('rollNo') != student_id]
        
        # Save updated students
        save_students(students)
        
        return jsonify({
            'success': True,
            'message': 'Student deleted successfully',
            'deletedId': student_id
        })
            
    except Exception as e:
        print(f"Error deleting student: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.filename.endswith('.xlsx'):
            return jsonify({'error': 'Only .xlsx files are allowed'}), 400
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath,dtype={'Student Contact': str, 'Parent No': str})
            if df.empty:
                os.remove(filepath)
                return jsonify({'error': 'Excel file is empty'}), 400
            
            print("Excel columns:", df.columns.tolist())
            
            # Column mapping for Excel to database fields
            column_mapping = {
                # Basic Info
                'Roll No': 'rollNo',
                'Reg No': 'regNo',
                'Section': 'classSection',
                'Student Name': 'studentName',
                'Father Name': 'fatherName',
                'Gender': 'gender',
                'DOB': 'dob',
                
                # Contact Info
                'Email': 'email',
                'Address': 'address',
                'Student Contact': 'studentContact',
                'Parent No': 'parentNo',
                
                # Personal Info
                'Aadhar No': 'aadharNo',
                'Blood Group': 'bloodGroup',
                'State': 'state',
                'District': 'district',
                'Religion': 'religion',
                'Category': 'category',
                'Caste': 'caste',
                'Income': 'income',
                'Category Applied': 'categoryApplied',
                
                # PUC Details
                'PUC/Equivalent Roll No': 'pucRollNo',
                'PUC/Equivalent Year of Completion': 'pucYear',
                'PUC/Equivalent Institute Name': 'pucInstitute',
                'PUC/Equivalent Total Marks': 'pucTotalMarks',
                'PUC/Equivalent Obtained Marks': 'pucObtainedMarks',
                'PUC/Equivalent Percentage/CGPA': 'pucPercentage',
                
                # Program Details
                'Program Name': 'programName',
                'Discipline 1': 'discipline1',
                'Language2': 'lang2',
                
                # ABC ID Details
                'ABC ID': 'abcId'
            }
            
            success_count = 0
            error_count = 0
            error_messages = []

            df['Student Contact'] = df['Student Contact'].str.replace(r'\.0$', '', regex=True)
            df['Parent No'] = df['Parent No'].str.replace(r'\.0$', '', regex=True)

            
            # Load existing students
            students = load_students()
            print(f"Loaded {len(students)} existing students")
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Initialize student data with default values
                    student_data = {
                        'classSection': 'N/A',
                        'collegeName': 'N/A',
                        'programName': 'N/A',
                        'discipline1': 'N/A',
                        'lang2': 'N/A',
                        'studentContact': 'N/A',
                        'email': 'N/A',
                        'pucRollNo': 'N/A',
                        'pucYear': 'N/A',
                        'pucInstitute': 'N/A',
                        'pucTotalMarks': '0',
                        'pucObtainedMarks': '0',
                        'pucPercentage': '0',
                        'abcId': 'N/A',
                        'abcIdCollected': 'No'
                    }
                    
                    # Map Excel columns to student fields
                    for col in df.columns:
                        if col in column_mapping:
                            value = row[col]
                            if pd.notna(value):  # Check if value is not NaN
                                value = str(value).strip()
                                if value.upper() not in ['NA', 'N/A', 'NULL', 'NONE', '', '-', 'EMPTY']:
                                    db_field = column_mapping.get(col)
                                    if db_field:
                                        student_data[db_field] = value
                    
                    # Validate required fields
                    if not student_data.get('rollNo'):
                        error_messages.append(f"Row {index + 2}: Missing Roll Number")
                        error_count += 1
                        continue
                    
                    # Check if student exists
                    student_exists = False
                    for i, student in enumerate(students):
                        if student['rollNo'] == student_data['rollNo']:
                            # Update existing student
                            students[i] = {**student, **student_data}
                            student_exists = True
                            print(f"Updated existing student: {student_data['rollNo']}")
                            break
                    
                    if not student_exists:
                        # Add new student
                        student_data['createdAt'] = datetime.now().isoformat()
                        students.append(student_data)
                        print(f"Added new student: {student_data['rollNo']}")
                    
                    success_count += 1
                    
                except Exception as e:
                    error_messages.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
                    print(f"Error in row {index + 2}: {str(e)}")
            
            # Save all students at once
            save_students(students)
            print(f"Saved {len(students)} total students")
            
            # Clean up
            os.remove(filepath)
            
            # Return appropriate message based on operation type
            return jsonify({
                'success': True,
                'message': f'Processed {len(df)} rows with {success_count} successes and {error_count} issues.',
                'stats': {
                    'total': len(df),
                    'success': success_count,
                    'errors': error_count
                },
                'error_messages': error_messages
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Error processing Excel file: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error handling file upload: {str(e)}'}), 500

@app.route('/delete_class/<class_section>', methods=['DELETE'])
def delete_class(class_section):
    try:
        if not class_section:
            return jsonify({
                'success': False,
                'error': 'Class section is required'
            }), 400
            
        students = load_students()
        students_to_delete = [s for s in students if s.get('classSection') == class_section]
        if not students_to_delete:
            return jsonify({
                'success': False,
                'error': f'No students found in class {class_section}'
            }), 404
            
        deleted_count = 0
        try:
            # Filter out students to be deleted
            students_filtered = [s for s in students if s.get('classSection') != class_section]
            
            # Save updated students
            save_students(students_filtered)
            
            deleted_count = len(students_to_delete)
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} students from class {class_section}',
                'deletedCount': deleted_count
            })
        except Exception as e:
            print(f"Error in batch delete: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database error while deleting class: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Error deleting class: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/edit_class/<class_section>', methods=['PUT'])
def edit_class(class_section):
    try:
        if not class_section:
            return jsonify({
                'success': False,
                'error': 'Class section is required'
            }), 400
            
        data = request.get_json()
        new_class_name = data.get('newClassName')
        
        if not new_class_name:
            return jsonify({
                'success': False,
                'error': 'New class name is required'
            }), 400
            
        students = load_students()
        students_to_update = [s for s in students if s.get('classSection') == class_section]
        if not students_to_update:
            return jsonify({
                'success': False,
                'error': f'No students found in class {class_section}'
            }), 404
            
        updated_count = 0
        try:
            # Update all students in a batch
            for i, student in enumerate(students_to_update):
                students[i] = {**student, **{'classSection': new_class_name}}
            
            # Save updated students
            save_students(students)
            
            updated_count = len(students_to_update)
            return jsonify({
                'success': True,
                'message': f'Successfully renamed class from {class_section} to {new_class_name}',
                'updatedCount': updated_count
            })
        except Exception as e:
            print(f"Error in batch update: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database error while renaming class: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Error renaming class: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/refresh_data', methods=['GET'])
def refresh_data():
    try:
        # Return the latest data
        students = load_students()
        student_list = []
        for student in students:
            student_data = student
            student_data['id'] = student['rollNo']
            student_list.append(student_data)
            
        return jsonify({
            'success': True,
            'data': student_list,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/verify_data_consistency', methods=['POST'])
def verify_data_consistency():
    try:
        data = request.json
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID is required'}), 400
            
        # Get the latest data from JSON
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == student_id), None)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        return jsonify({
            'success': True,
            'data': student,
            'last_updated': student.get('updatedAt', None)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compare_student_data', methods=['POST'])
def compare_student_data():
    try:
        data = request.json
        excel_data = data.get('excelData', {})
        roll_no = excel_data.get('rollNo')
        
        if not roll_no:
            return jsonify({'error': 'Roll number is required'}), 400
            
        # Get student from JSON
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == roll_no), None)
        
        if not student:
            return jsonify({'error': 'Student not found in JSON'}), 404
            
        # Compare fields and find differences
        differences = {}
        for field, excel_value in excel_data.items():
            if field in student:
                db_value = str(student[field]).strip()
                excel_value = str(excel_value).strip()
                
                # Skip empty or matching values
                if excel_value and excel_value != 'Empty' and excel_value != db_value:
                    differences[field] = {
                        'database': db_value,
                        'excel': excel_value,
                        'field_name': field.replace('_', ' ').title()  # Format field name for display
                    }
        
        # Return comparison results with student info
        return jsonify({
            'hasDifferences': len(differences) > 0,
            'differences': differences,
            'student_info': {
                'rollNo': roll_no,
                'studentName': student.get('studentName', 'N/A'),
                'classSection': student.get('classSection', 'N/A')
            },
            'message': f'Found {len(differences)} differences for {student.get("studentName", "Student")}' if differences else 'No differences found'
        })
        
    except Exception as e:
        print(f"Error in compare_student_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/update_student_data', methods=['POST'])
def update_student_data():
    try:
        data = request.json
        roll_no = data.get('rollNo')
        updates = data.get('updates', {})
        
        if not roll_no or not updates:
            return jsonify({'error': 'Roll number and updates are required'}), 400
            
        # Get student data
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == roll_no), None)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        # Update only the specified fields
        updated_student = {**student, **updates, 'lastUpdated': datetime.now().isoformat()}
        
        # Update the student data
        for i, s in enumerate(students):
            if s['rollNo'] == roll_no:
                students[i] = updated_student
                break
        
        # Save updated students
        save_students(students)
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {len(updates)} field(s)',
            'updatedFields': list(updates.keys())
        })
        
    except Exception as e:
        print(f"Error in update_student_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_template')
def download_template():
    try:
        # Create a new workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Student Data Template"

        # Define headers
        headers = [
            'Roll No', 'Reg No', 'Section', 'Student Name', 'Father Name', 'Gender', 'DOB',
            'Email', 'Address', 'Student Contact', 'Parent No', 'Aadhar No', 'Blood Group',
            'State', 'District', 'Religion', 'Category', 'Caste', 'Income', 'Category Applied',
            'PUC/Equivalent Roll No', 'PUC/Equivalent Year of Completion', 'PUC/Equivalent Institute Name',
            'PUC/Equivalent Total Marks', 'PUC/Equivalent Obtained Marks', 'PUC/Equivalent Percentage/CGPA',
            'Program Name', 'Discipline 1', 'Language2', 'ABC ID'
        ]

        # Add headers to worksheet
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

        # Add data validation for specific columns
        gender_validation = DataValidation(
            type="list",
            formula1='"Male,Female,Other"',
            allow_blank=True
        )
        ws.add_data_validation(gender_validation)
        gender_validation.add(f"F2:F1000")  # Apply to Gender column

        # Save to BytesIO object
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='student_template.xlsx'
        )

    except Exception as e:
        print(f"Error creating template: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug/profile-images')
def debug_profile_images():
    """Debug route to check profile image paths"""
    try:
        # Get all students
        students = load_students()
        
        # Extract profile image information
        image_info = []
        for student in students:
            info = {
                'rollNo': student.get('rollNo', 'N/A'),
                'studentName': student.get('studentName', 'N/A'),
                'hasProfileImage': 'profileImage' in student,
                'profileImagePath': student.get('profileImage', 'None')
            }
            
            # Check if file exists on disk
            if info['hasProfileImage'] and info['profileImagePath']:
                full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', student['profileImage'])
                info['fileExists'] = os.path.exists(full_path)
                info['fullPath'] = full_path
            else:
                info['fileExists'] = False
                info['fullPath'] = 'N/A'
                
            image_info.append(info)
            
        # Check upload folder
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
        files_in_folder = []
        if os.path.exists(upload_folder):
            files_in_folder = os.listdir(upload_folder)
            
        return jsonify({
            'students_with_images': sum(1 for s in image_info if s['hasProfileImage']),
            'total_students': len(image_info),
            'image_info': image_info,
            'upload_folder': upload_folder,
            'files_in_upload_folder': files_in_folder
        }), 200
        
    except Exception as e:
        print(f"Error in debug_profile_images: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/bulk_image_upload', methods=['POST'])
def bulk_image_upload():
    """Handle bulk upload of student profile images"""
    try:
        # Check if any files were uploaded
        if 'images' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
            
        uploaded_files = request.files.getlist('images')
        if len(uploaded_files) == 0:
            return jsonify({'error': 'No files selected'}), 400
            
        # Load all students to match roll numbers
        students = load_students()
        student_roll_numbers = {student.get('rollNo', '').lower(): student for student in students}
        
        # Set up upload folder
        upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
        results = {
            'success': [],
            'errors': []
        }
        
        # Process each file
        for file in uploaded_files:
            try:
                # Get the original filename and extract roll number
                original_filename = secure_filename(file.filename)
                
                # Try different methods to extract roll number:
                # 1. Use the filename without extension as roll number
                filename_without_ext = os.path.splitext(original_filename)[0].lower()
                
                # 2. Check if file matches an existing roll number
                matching_roll = None
                if filename_without_ext in student_roll_numbers:
                    matching_roll = filename_without_ext
                
                # If no match found, skip this file
                if not matching_roll:
                    results['errors'].append({
                        'filename': original_filename,
                        'error': f'No student found with roll number matching filename: {filename_without_ext}'
                    })
                    continue
                    
                # Get the student and determine file extension
                student = student_roll_numbers[matching_roll]
                file_ext = os.path.splitext(original_filename)[1].lower()
                if not file_ext:
                    file_ext = '.jpg'  # Default to jpg if no extension
                
                # Create the new filename
                new_filename = f"{matching_roll}{file_ext}"
                file_path = os.path.join(upload_path, new_filename)
                
                # Save the file
                file.save(file_path)
                
                # Update the student record with the image path
                image_rel_path = f"uploads/{new_filename}"
                
                # Find the student in the original list and update
                for s in students:
                    if s.get('rollNo', '').lower() == matching_roll:
                        s['profileImage'] = image_rel_path
                        break
                
                # Add to success results
                results['success'].append({
                    'original_filename': original_filename,
                    'roll_number': matching_roll,
                    'new_filename': new_filename,
                    'image_path': image_rel_path
                })
                
            except Exception as e:
                results['errors'].append({
                    'filename': original_filename if 'original_filename' in locals() else 'unknown',
                    'error': str(e)
                })
        
        # Save updated student data
        save_students(students)
        
        # Return results
        return jsonify({
            'success': True,
            'message': f"Successfully processed {len(results['success'])} images with {len(results['errors'])} errors",
            'results': results
        })
        
    except Exception as e:
        print(f"Error in bulk_image_upload: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
