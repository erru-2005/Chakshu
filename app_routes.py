from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from student_data import (
    get_student_by_barcode, 
    check_duplicate_student, 
    add_student, 
    get_all_students, 
    update_student, 
    delete_student, 
    search_students
)
from excel_handler import (
    process_uploaded_file, 
    import_students_from_excel, 
    export_students_to_excel, 
    update_students_from_excel, 
    compare_excel_with_database
)
from flask import current_app

# Create Flask app
app = Flask(__name__)

# Add secret key for flash messages
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_for_development')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # cache static files for a day

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
PROFILE_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PROFILE_UPLOAD_FOLDER):
    os.makedirs(PROFILE_UPLOAD_FOLDER)
    
# Allowed file extensions for profile images
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _resolve_profile_image_internal(profile_image, roll_no):
    """Return relative static path for an existing profile image.
    Tries the stored path first, then guesses by roll number with common extensions and cases.
    """
    try:
        static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        candidates = []
        if profile_image:
            stored = profile_image.replace('\\', '/')
            candidates.append(os.path.join(static_root, stored))
            # If JSON still points to .webp/.jpeg/.png but we migrated to .webp, try .webp too
            base, ext = os.path.splitext(stored)
            candidates.append(os.path.join(static_root, f"{base}.webp"))
        roll_str = (str(roll_no or '').strip())
        if roll_str:
            for ext in ('webp', 'jpeg', 'png'):
                # lowercase and uppercase variants
                candidates.append(os.path.join(static_root, 'uploads', f"{roll_str.lower()}.{ext}"))
                candidates.append(os.path.join(static_root, 'uploads', f"{roll_str.upper()}.{ext}"))
            # Also check webp
            candidates.append(os.path.join(static_root, 'uploads', f"{roll_str.lower()}.webp"))
            candidates.append(os.path.join(static_root, 'uploads', f"{roll_str.upper()}.webp"))
        for abs_path in candidates:
            if os.path.exists(abs_path):
                return os.path.relpath(abs_path, static_root).replace('\\', '/')
    except Exception:
        pass
    return None

def _resolve_profile_image_thumb(profile_image, roll_no):
    """Return relative static path for a small thumbnail version if available.
    Prefers WebP thumbnail, falls back to normal resolver.
    """
    try:
        static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        roll_str = (str(roll_no or '').strip())
        # Prefer webp thumbnails
        thumb_webp = os.path.join(static_root, 'uploads', 'thumbs', f"{roll_str.lower()}_thumb.webp")
        if os.path.exists(thumb_webp):
            return os.path.relpath(thumb_webp, static_root).replace('\\', '/')
    except Exception:
        pass
    return _resolve_profile_image_internal(profile_image, roll_no)

@app.context_processor
def inject_image_resolver():
    return {
        'resolve_profile_image': _resolve_profile_image_internal,
        'resolve_profile_image_thumb': _resolve_profile_image_thumb
    }

def _avatar_style(name):
    try:
        palette = [
            'linear-gradient(135deg, hsla(210, 85%, 40%, 0.90), hsla(210, 90%, 55%, 0.75))',  # blue
            'linear-gradient(135deg, hsla(260, 70%, 45%, 0.90), hsla(260, 80%, 60%, 0.75))',  # purple
            'linear-gradient(135deg, hsla(340, 75%, 45%, 0.90), hsla(340, 85%, 60%, 0.75))',  # pink
            'linear-gradient(135deg, hsla(28, 85%, 50%, 0.90), hsla(28, 95%, 60%, 0.75))',   # orange
            'linear-gradient(135deg, hsla(140, 55%, 40%, 0.90), hsla(140, 65%, 50%, 0.75))', # green
            'linear-gradient(135deg, hsla(190, 65%, 40%, 0.90), hsla(190, 75%, 55%, 0.75))', # teal
            'linear-gradient(135deg, hsla(50, 85%, 45%, 0.90), hsla(50, 95%, 55%, 0.75))',   # yellow
            'linear-gradient(135deg, hsla(280, 70%, 45%, 0.90), hsla(280, 80%, 60%, 0.75))', # indigo
        ]
        s = str(name or '').lower()
        if not s:
            return palette[0]
        h = 0
        for ch in s:
            h = ((h << 5) - h) + ord(ch)
            h &= 0xFFFFFFFF
        return palette[abs(h) % len(palette)]
    except Exception:
        return 'linear-gradient(135deg, hsla(210, 85%, 40%, 0.90), hsla(210, 90%, 55%, 0.75))'

def _avatar_theme(name):
    """Return a dict with bg and fg (text) color ensuring readability."""
    # Backgrounds from a diverse professional palette
    palettes = [
        ("linear-gradient(135deg, hsla(210, 85%, 40%, 0.90), hsla(210, 90%, 55%, 0.75))", "#ffffff"), # blue -> white text
        ("linear-gradient(135deg, hsla(260, 70%, 45%, 0.90), hsla(260, 80%, 60%, 0.75))", "#ffffff"), # purple -> white
        ("linear-gradient(135deg, hsla(340, 75%, 45%, 0.90), hsla(340, 85%, 60%, 0.75))", "#ffffff"), # pink -> white
        ("linear-gradient(135deg, hsla(28, 85%, 50%, 0.90), hsla(28, 95%, 60%, 0.75))", "#1f2937"),  # orange -> dark text
        ("linear-gradient(135deg, hsla(140, 55%, 40%, 0.90), hsla(140, 65%, 50%, 0.75))", "#ffffff"), # green -> white
        ("linear-gradient(135deg, hsla(190, 65%, 40%, 0.90), hsla(190, 75%, 55%, 0.75))", "#ffffff"), # teal -> white
        ("linear-gradient(135deg, hsla(50, 85%, 45%, 0.90), hsla(50, 95%, 55%, 0.75))", "#1f2937"),   # yellow -> dark
        ("linear-gradient(135deg, hsla(280, 70%, 45%, 0.90), hsla(280, 80%, 60%, 0.75))", "#ffffff"), # indigo -> white
    ]
    s = str(name or '').lower()
    if not s:
        return { 'bg': palettes[0][0], 'fg': palettes[0][1] }
    h = 0
    for ch in s:
        h = ((h << 5) - h) + ord(ch)
        h &= 0xFFFFFFFF
    bg, fg = palettes[abs(h) % len(palettes)]
    return { 'bg': bg, 'fg': fg }

@app.context_processor
def inject_avatar_style():
    return {
        'avatar_style': _avatar_style,
        'avatar_theme': _avatar_theme
    }

def save_profile_image(file, roll_no):
    """Save and compress student profile image with roll number as filename."""
    if file and allowed_file(file.filename):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        roll_no_lower = str(roll_no).strip().lower()
        filename = f"{roll_no_lower}.{file_ext}"
        file_path = os.path.join(PROFILE_UPLOAD_FOLDER, filename)

        # Ensure destination folder exists
        if not os.path.exists(PROFILE_UPLOAD_FOLDER):
            os.makedirs(PROFILE_UPLOAD_FOLDER)

        # Process with Pillow: resize and compress
        try:
            file.stream.seek(0)
            with Image.open(file.stream) as img:
                # Convert mode for JPEG if needed
                if img.mode in ("P", "RGBA"):
                    img = img.convert("RGB")

                # Resize to a reasonable max dimension to reduce bytes
                max_size = (800, 800)
                img.thumbnail(max_size, Image.LANCZOS)

                save_kwargs = {}
                # Save main as WEBP for smaller size
                filename = f"{roll_no_lower}.webp"
                file_path = os.path.join(PROFILE_UPLOAD_FOLDER, filename)
                img.save(file_path, format='WEBP', quality=80, method=6)

                # Also generate fast WebP thumbnail (256x256)
                try:
                    thumb_dir = os.path.join(PROFILE_UPLOAD_FOLDER, 'thumbs')
                    if not os.path.exists(thumb_dir):
                        os.makedirs(thumb_dir)
                    thumb_path = os.path.join(thumb_dir, f"{roll_no_lower}_thumb.webp")
                    thumb = img.copy()
                    thumb.thumbnail((256, 256), Image.LANCZOS)
                    thumb.save(thumb_path, format='WEBP', quality=75, method=6)
                except Exception:
                    pass

        except Exception:
            # If processing fails, fallback to saving original
            file.stream.seek(0)
            file.save(file_path)

        return f"uploads/{filename}"
    return None

# Routes
@app.route('/')
def index():
    """Render the student form page"""
    return render_template('student_form.html')

@app.route('/search_barcode', methods=['POST'])
def search_barcode():
    """Search for a student by barcode (roll number)"""
    try:
        data = request.json
        barcode = data.get('barcode')
        
        if not barcode:
            return jsonify({'error': 'Barcode is required'}), 400

        student_data = get_student_by_barcode(barcode)
        
        if student_data:
            return jsonify(student_data), 200
        else:
            return jsonify({'error': f'No student found with Roll Number: {barcode}'}), 404

    except Exception as e:
        print(f"Error in search_barcode: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    """Check if a student with given roll number or registration number already exists"""
    try:
        data = request.json
        roll_no = data.get('rollNo')
        reg_no = data.get('regNo')
        
        if not roll_no:
            return jsonify({'error': 'Roll number is required'}), 400

        result = check_duplicate_student(roll_no, reg_no)
        return jsonify(result), 200

    except Exception as e:
        print(f"Error in check_duplicate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/submit', methods=['POST'])
def submit():
    """Submit a new student"""
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
            
            # Handle profile image upload
            if 'profileImage' in request.files:
                profile_image = request.files['profileImage']
                if profile_image and profile_image.filename:
                    # Only process if roll number is provided
                    if 'rollNo' in student_data and student_data['rollNo']:
                        # Save the image and get the path
                        image_path = save_profile_image(profile_image, student_data['rollNo'])
                        if image_path:
                            student_data['profileImage'] = image_path
        
        # Remove None and empty string values
        student_data = {k: v for k, v in student_data.items() if v is not None and v != ''}

        # Submit the student data
        result = add_student(student_data)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        else:
            return jsonify(result), 200

    except Exception as e:
        print(f"Error in submit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/manage')
def manage_students():
    """Render the student management page"""
    try:
        result = get_all_students()
        
        return render_template('student_management.html', 
                          students=result['students'],
                          students_by_class=result['students_by_class'],
                          has_students=result['has_students'])
    except Exception as e:
        print(f"Error in manage_students: {str(e)}")
        # Return empty lists instead of error
        return render_template('student_management.html',
                          students=[],
                          students_by_class={},
                          has_students=False)

@app.route('/search_students', methods=['POST'])
def search_students_route():
    """Search for students based on query string and filter type"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        filter_type = data.get('filter', 'all')
        
        if not query:
            return jsonify({'students': []}), 200

        students = search_students(query, filter_type)
        return jsonify({'students': students}), 200

    except Exception as e:
        print(f"Error in search_students: {str(e)}")
        return jsonify({'error': str(e), 'students': []}), 500

@app.route('/get_student_details/<student_id>')
def get_student_details(student_id):
    """Get details of a specific student"""
    try:
        # Get student using the roll number as ID
        student = get_student_by_barcode(student_id)
        
        if student:
            return jsonify(student), 200
        else:
            return jsonify({'error': f'Student with ID {student_id} not found'}), 404

    except Exception as e:
        print(f"Error in get_student_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit a student's information"""
    try:
        if request.method == 'GET':
            student = get_student_by_barcode(student_id)
            if student:
                return render_template('student_update.html', student=student)
            else:
                flash(f'Student with ID {student_id} not found', 'error')
                return redirect(url_for('manage_students'))
        elif request.method == 'POST':
            # Get data from form
            updated_data = {}
            for key in request.form:
                updated_data[key] = request.form.get(key)
                
            # Handle profile image upload
            if 'profileImage' in request.files:
                profile_image = request.files['profileImage']
                if profile_image and profile_image.filename:
                    # Save the image and get the path
                    image_path = save_profile_image(profile_image, student_id)
                    if image_path:
                        updated_data['profileImage'] = image_path
                
            # Remove None and empty string values
            updated_data = {k: v for k, v in updated_data.items() if v is not None and v != ''}
            
            result = update_student(student_id, updated_data)
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(result['message'], 'error')
                
            return redirect(url_for('manage_students'))

    except Exception as e:
        print(f"Error in edit_student: {str(e)}")
        flash(f'Error updating student: {str(e)}', 'error')
        return redirect(url_for('manage_students'))

@app.route('/delete_student/<student_id>', methods=['DELETE'])
def delete_student_route(student_id):
    """Delete a student"""
    try:
        result = delete_student(student_id)
        return jsonify(result), 200 if result['success'] else 404

    except Exception as e:
        print(f"Error in delete_student: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload an Excel file with student data"""
    try:
        # Process uploaded file
        file = request.files.get('file')
        result = process_uploaded_file(file, UPLOAD_FOLDER)
        
        if not result['success']:
            return jsonify(result), 400
            
        # Option to import directly
        import_now = request.form.get('importNow') == 'true'
        
        if import_now:
            import_result = import_students_from_excel(result['file_path'])
            
            if import_result['success']:
                # Remove file after successful import
                os.remove(result['file_path'])
                
                return jsonify({
                    'success': True,
                    'message': import_result['message'],
                    'details': import_result['details']
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': import_result['message']
                }), 400
        else:
            # Return file info and preview for confirmation
            return jsonify(result), 200

    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/export', methods=['GET'])
def export_students():
    """Export all students to Excel file"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(UPLOAD_FOLDER, f"students_export_{timestamp}.xlsx")
        
        result = export_students_to_excel(output_path)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"Error in export_students: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_from_excel', methods=['POST'])
def update_from_excel():
    """Update student data from Excel file"""
    try:
        # Process uploaded file
        file = request.files.get('file')
        result = process_uploaded_file(file, UPLOAD_FOLDER)
        
        if not result['success']:
            return jsonify(result), 400
            
        # Get update options
        update_option = request.form.get('updateOption', 'all')  # 'all', 'missing', 'different'
        
        # Update from Excel
        update_result = update_students_from_excel(result['file_path'], update_option)
        
        # Clean up
        os.remove(result['file_path'])
        
        if update_result['success']:
            return jsonify(update_result), 200
        else:
            return jsonify(update_result), 400

    except Exception as e:
        print(f"Error in update_from_excel: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/compare_excel', methods=['POST'])
def compare_excel():
    """Compare Excel data with database"""
    try:
        # Process uploaded file
        file = request.files.get('file')
        result = process_uploaded_file(file, UPLOAD_FOLDER)
        
        if not result['success']:
            return jsonify(result), 400
            
        # Compare with database
        compare_result = compare_excel_with_database(result['file_path'])
        
        # Clean up
        os.remove(result['file_path'])
        
        if compare_result['success']:
            return jsonify(compare_result), 200
        else:
            return jsonify(compare_result), 400

    except Exception as e:
        print(f"Error in compare_excel: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/debug/profile-images')
def debug_profile_images():
    """Debug route to check profile image paths"""
    try:
        # Get all students
        all_students = get_all_students()
        
        # Extract profile image information
        image_info = []
        for student in all_students['students']:
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
            
        return jsonify({
            'students_with_images': sum(1 for s in image_info if s['hasProfileImage']),
            'total_students': len(image_info),
            'image_info': image_info,
            'profile_upload_folder': PROFILE_UPLOAD_FOLDER,
            'static_folder': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        }), 200
        
    except Exception as e:
        print(f"Error in debug_profile_images: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000) 