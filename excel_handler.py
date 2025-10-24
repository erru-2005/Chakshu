import pandas as pd
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from student_data import db, add_student, update_student

def validate_excel_file(file_path):
    """Validate an Excel file"""
    try:
        df = pd.read_excel(file_path)
        
        # Check required columns
        required_columns = ['rollNo', 'classSection']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'valid': False,
                'message': f"Missing required columns: {', '.join(missing_columns)}"
            }
            
        # Check for empty roll numbers
        empty_roll_nos = df[df['rollNo'].isna() | (df['rollNo'] == '')].index.tolist()
        if empty_roll_nos:
            row_numbers = [i+2 for i in empty_roll_nos]  # +2 for header row and 0-indexing
            return {
                'valid': False,
                'message': f"Empty roll numbers found in rows: {', '.join(map(str, row_numbers))}"
            }
            
        return {
            'valid': True,
            'message': 'File is valid',
            'data': df
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f"Error validating file: {str(e)}"
        }

def process_uploaded_file(file, upload_folder):
    """Process an uploaded file and save it to the upload folder"""
    try:
        if not file:
            return {
                'success': False, 
                'message': 'No file uploaded'
            }
            
        filename = secure_filename(file.filename)
        if not filename:
            return {
                'success': False, 
                'message': 'Invalid filename'
            }
            
        # Check file extension
        if not filename.endswith(('.xlsx', '.xls')):
            return {
                'success': False, 
                'message': 'Only Excel files (.xlsx, .xls) are allowed'
            }
            
        # Create upload folder if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file with timestamp to prevent overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name, extension = os.path.splitext(filename)
        new_filename = f"{base_name}_{timestamp}{extension}"
        file_path = os.path.join(upload_folder, new_filename)
        
        file.save(file_path)
        
        # Validate Excel file
        validation = validate_excel_file(file_path)
        if not validation['valid']:
            os.remove(file_path)  # Remove invalid file
            return {
                'success': False,
                'message': validation['message']
            }
            
        return {
            'success': True,
            'message': 'File uploaded successfully',
            'file_path': file_path,
            'preview': validation['data'].head(5).to_dict('records')
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing file: {str(e)}'
        }

def import_students_from_excel(file_path):
    """Import students from Excel file to Firestore"""
    validation = validate_excel_file(file_path)
    if not validation['valid']:
        return validation
        
    df = validation['data']
    
    # Initialize counters for reports
    total_rows = len(df)
    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []
    skipped = []
    
    # Process each row
    for index, row in df.iterrows():
        try:
            row_dict = row.dropna().to_dict()
            
            # Convert numeric columns to string to prevent scientific notation issues
            for key in row_dict:
                if isinstance(row_dict[key], (int, float)):
                    row_dict[key] = str(int(row_dict[key]) if row_dict[key] == int(row_dict[key]) else row_dict[key])
            
            # Skip rows without roll number
            if 'rollNo' not in row_dict or not row_dict['rollNo']:
                skip_reason = f"Row {index+2}: Missing roll number"
                skipped.append(skip_reason)
                skip_count += 1
                continue
                
            # Check if student already exists
            roll_no = row_dict['rollNo']
            doc_ref = db.collection('students').document(roll_no)
            doc = doc_ref.get()
            
            if doc.exists:
                skip_reason = f"Row {index+2}: Student with roll number {roll_no} already exists"
                skipped.append(skip_reason)
                skip_count += 1
                continue
                
            # Add timestamp
            row_dict['createdAt'] = datetime.now().isoformat()
            
            # Create new student document
            doc_ref.set(row_dict)
            success_count += 1
            
        except Exception as e:
            error_msg = f"Row {index+2}: {str(e)}"
            errors.append(error_msg)
            error_count += 1
    
    return {
        'success': True,
        'message': f"Import completed: {success_count} added, {skip_count} skipped, {error_count} errors",
        'details': {
            'total': total_rows,
            'success': success_count,
            'skipped': skip_count,
            'error': error_count,
            'skipped_details': skipped,
            'error_details': errors
        }
    }

def export_students_to_excel(output_path=None):
    """Export all students from Firestore to Excel file"""
    try:
        # Get all students
        students_ref = db.collection('students')
        students = students_ref.stream()
        
        students_list = []
        for doc in students:
            student_data = doc.to_dict()
            student_data['id'] = doc.id
            students_list.append(student_data)
            
        if not students_list:
            return {
                'success': False,
                'message': 'No students found to export'
            }
            
        # Convert to DataFrame
        df = pd.DataFrame(students_list)
        
        # Generate output filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"students_export_{timestamp}.xlsx"
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Write to Excel
        df.to_excel(output_path, index=False)
        
        return {
            'success': True,
            'message': f'Successfully exported {len(students_list)} students to {output_path}',
            'file_path': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error exporting students: {str(e)}'
        }

def update_students_from_excel(file_path, update_option='all'):
    """Update student data from Excel file"""
    validation = validate_excel_file(file_path)
    if not validation['valid']:
        return validation
        
    df = validation['data']
    
    # Get current students
    students_ref = db.collection('students')
    students = students_ref.stream()
    db_students = {}
    
    for doc in students:
        student_data = doc.to_dict()
        student_data['id'] = doc.id
        db_students[student_data['rollNo']] = student_data
    
    # Process updates
    updated_count = 0
    added_count = 0
    skipped_count = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            row_dict = row.dropna().to_dict()
            
            # Convert numeric values to proper format
            for key in row_dict:
                if isinstance(row_dict[key], (int, float)):
                    row_dict[key] = str(int(row_dict[key]) if row_dict[key] == int(row_dict[key]) else row_dict[key])
            
            if 'rollNo' not in row_dict or not row_dict['rollNo']:
                skipped_count += 1
                continue
                
            roll_no = row_dict['rollNo']
            
            if roll_no in db_students:
                # Update existing student
                if update_option in ['all', 'different']:
                    update_result = update_student(roll_no, row_dict)
                    if update_result.get('success'):
                        updated_count += 1
                    else:
                        errors.append(f"Row {index+2}: {update_result.get('message')}")
                        skipped_count += 1
                else:
                    skipped_count += 1
            else:
                # Add new student
                if update_option in ['all', 'missing']:
                    add_result = add_student(row_dict)
                    if add_result.get('success'):
                        added_count += 1
                    else:
                        errors.append(f"Row {index+2}: {add_result.get('error')}")
                        skipped_count += 1
                else:
                    skipped_count += 1
                    
        except Exception as e:
            errors.append(f"Row {index+2}: {str(e)}")
            skipped_count += 1
            
    return {
        'success': True,
        'message': f"Update completed: {updated_count} updated, {added_count} added, {skipped_count} skipped",
        'details': {
            'updated': updated_count,
            'added': added_count,
            'skipped': skipped_count,
            'errors': errors
        }
    }

def compare_excel_with_database(file_path):
    """Compare student data in database with uploaded Excel file"""
    validation = validate_excel_file(file_path)
    if not validation['valid']:
        return validation
        
    df = validation['data']
    
    # Get students from database
    students_ref = db.collection('students')
    db_students = {}
    
    for doc in students_ref.stream():
        student_data = doc.to_dict()
        student_data['id'] = doc.id
        db_students[student_data['rollNo']] = student_data
    
    # Compare data
    missing_in_db = []
    missing_in_excel = []
    different_values = []
    
    # Check Excel against DB
    for index, row in df.iterrows():
        try:
            if 'rollNo' not in row or pd.isna(row['rollNo']):
                continue
                
            roll_no = str(int(row['rollNo']) if pd.notna(row['rollNo']) and row['rollNo'] == int(row['rollNo']) else row['rollNo'])
            
            if roll_no not in db_students:
                missing_in_db.append(roll_no)
            else:
                # Compare values
                for column in df.columns:
                    if column in db_students[roll_no] and pd.notna(row[column]):
                        excel_val = str(int(row[column]) if pd.notna(row[column]) and row[column] == int(row[column]) else row[column])
                        db_val = str(db_students[roll_no][column])
                        
                        if excel_val != db_val:
                            different_values.append({
                                'rollNo': roll_no,
                                'field': column,
                                'db_value': db_val,
                                'excel_value': excel_val
                            })
        except Exception as e:
            print(f"Error comparing row {index+2}: {str(e)}")
    
    # Check DB against Excel
    excel_roll_nos = []
    for _, row in df.iterrows():
        if 'rollNo' in row and pd.notna(row['rollNo']):
            roll_no = str(int(row['rollNo']) if pd.notna(row['rollNo']) and row['rollNo'] == int(row['rollNo']) else row['rollNo'])
            excel_roll_nos.append(roll_no)
    
    for roll_no in db_students:
        if roll_no not in excel_roll_nos:
            missing_in_excel.append(roll_no)
                
    return {
        'success': True,
        'comparison': {
            'missing_in_db': missing_in_db,
            'missing_in_excel': missing_in_excel,
            'different_values': different_values
        }
    } 