from flask import Flask, render_template, request, jsonify, url_for, flash, redirect
import os
from dotenv import load_dotenv
import json
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime

# Load environment variables
load_dotenv()

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

# Student data functions
def get_student_by_barcode(barcode):
    """Search for student with matching roll number (since barcode = roll number)"""
    if not barcode:
        return None
        
    students = load_students()
    return next((s for s in students if s.get('rollNo') == barcode), None)

def check_duplicate_student(roll_no, reg_no=None):
    """Check if a student with the given roll number or registration number already exists"""
    if not roll_no:
        return False
        
    students = load_students()
    
    # Check for duplicate roll number
    if any(s.get('rollNo') == roll_no for s in students):
        return True
        
    # Check for duplicate registration number if provided
    if reg_no and any(s.get('regNo') == reg_no for s in students):
        return True
        
    return False

def add_student(student_data):
    """Add a new student to the database"""
    try:
        # Check for duplicates before saving
        students = load_students()
        
        # First check if student with this roll number already exists
        if any(s.get('rollNo') == student_data['rollNo'] for s in students):
            return False, f'Student with Roll Number {student_data["rollNo"]} already exists!'
            
        # Check for duplicate registration number if provided
        if student_data.get('regNo') and any(s.get('regNo') == student_data['regNo'] for s in students):
            return False, f'Student with Registration Number {student_data["regNo"]} already exists!'
            
        # Add timestamp
        student_data['createdAt'] = datetime.now().isoformat()
        
        # Save to JSON
        students.append(student_data)
        save_students(students)
        
        return True, f"New student data saved for roll number: {student_data['rollNo']}"
        
    except Exception as e:
        print(f"Error saving student data: {str(e)}")
        return False, f'Database error: {str(e)}'

def get_all_students():
    """Get all students from the database"""
    try:
        students = load_students()
        return students
    except Exception as e:
        print(f"Error getting all students: {str(e)}")
        return []

def update_student(student_id, updated_data):
    """Update an existing student's data"""
    try:
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == student_id), None)
        
        if not student:
            return False, 'Student not found'
            
        # Update the student data
        for i, s in enumerate(students):
            if s['rollNo'] == student_id:
                students[i] = {**s, **updated_data, 'updatedAt': datetime.now().isoformat()}
                break
                
        # Save updated students
        save_students(students)
        
        return True, 'Student updated successfully'
        
    except Exception as e:
        print(f"Error updating student: {str(e)}")
        return False, f'Database error: {str(e)}'

def delete_student(student_id):
    """Delete a student from the database"""
    try:
        students = load_students()
        student = next((s for s in students if s.get('rollNo') == student_id), None)
        
        if not student:
            return False, 'Student not found'
            
        # Remove the student from the list
        students = [s for s in students if s.get('rollNo') != student_id]
        
        # Save updated students
        save_students(students)
        
        return True, 'Student deleted successfully'
        
    except Exception as e:
        print(f"Error deleting student: {str(e)}")
        return False, f'Database error: {str(e)}'

def search_students(query, filter_type='all'):
    """Search for students based on query and filter type"""
    try:
        students = load_students()
        query = query.lower().strip()
        
        # Filter students based on case-insensitive search
        filtered_students = []
        seen_ids = set()
        
        for student in students:
            student_name = student.get('studentName', '').lower()
            roll_no = student.get('rollNo', '').lower()
            class_section = student.get('classSection', '').lower()
            
            # Apply different search logic based on filter type
            match_found = False
            
            if filter_type == 'all':
                match_found = (query in student_name or 
                             query in roll_no or 
                             query in class_section)
            elif filter_type == 'name':
                match_found = query in student_name
            elif filter_type == 'roll':
                match_found = query in roll_no
            elif filter_type == 'class':
                match_found = query in class_section
                
            if match_found and student['rollNo'] not in seen_ids:
                filtered_students.append({
                    'id': student['rollNo'],
                    'studentName': student.get('studentName', ''),
                    'rollNo': student.get('rollNo', ''),
                    'classSection': student.get('classSection', '')
                })
                seen_ids.add(student['rollNo'])
                
        return filtered_students[:20]  # Limit to 20 results
        
    except Exception as e:
        print(f"Error searching students: {str(e)}")
        return [] 