# Chakshu - Smart Student Registration System

A modular, Firebase-integrated system for student data management with Excel import/export capabilities and real-time validation.

## Features

- **Modular Architecture**: Clean separation of concerns across multiple Python files
- **Excel Smart Processing**: Validate and import student data from Excel files
- **Firebase Backend**: Real-time data sync and reliable storage
- **Manual Entry & Editing**: Add and update student records via intuitive web interface
- **Data Validation**: Detect duplicates and validate required fields

## Project Structure

```
Chakshu/
├── app_routes.py        # Flask routes and API endpoints
├── student_data.py      # Student data model and database operations
├── excel_handler.py     # Excel file processing and validation
├── run.py               # Main application entry point
├── build_exe.py         # Script to build Windows executable
├── templates/           # HTML templates
├── static/              # Static assets (CSS, JS, images)
├── uploads/             # Folder for uploaded/exported Excel files
└── serviceAccountKey.json  # Firebase credentials
```

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Firebase account with Firestore database
- Firebase service account key (JSON file)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/chakshu.git
   cd chakshu
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Place your Firebase service account key in the project root as `serviceAccountKey.json`

4. Create a `.env` file in the project root with the following content:
   ```
   SECRET_KEY=your_secret_key_here
   ```

### Running the Application

Run the development server:
```
python run.py
```

The application will be available at http://localhost:5000

## Usage Guide

### Adding Students

1. Navigate to the home page
2. Fill out the student form with required information
3. Click "Submit" to save the student data

### Importing Students from Excel

1. Navigate to the management page
2. Click "Upload Excel" button
3. Select your Excel file (.xlsx or .xls)
4. Review the preview and click "Import" to confirm

### Updating Students

1. Navigate to the management page
2. Find the student in the list and click "Edit"
3. Update the information and click "Save Changes"

### Exporting Student Data

1. Navigate to the management page
2. Click "Export to Excel" button
3. The system will generate an Excel file with all student data

## Building Windows Executable

To create a standalone Windows executable:

1. Install cx_Freeze:
   ```
   pip install cx_Freeze
   ```

2. Run the build script:
   ```
   python build_exe.py build
   ```

3. Find the executable in the `build` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project uses Flask for web framework
- Firebase for backend data storage
- Pandas for Excel processing
