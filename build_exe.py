import sys
import os
from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": [
        "flask", 
        "firebase_admin", 
        "pandas", 
        "werkzeug",
        "openpyxl",
        "dotenv",
        "jinja2",
        "datetime"
    ],
    "include_files": [
        ("templates", "templates"),
        ("static", "static"),
        ("serviceAccountKey.json", "serviceAccountKey.json"),
        (".env", ".env"),
        ("uploads", "uploads"),
    ],
    "excludes": ["tkinter", "unittest", "email", "http", "html", "xml", "pydoc"],
    "include_msvcr": True,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use this for a Windows GUI application

setup(
    name="Chakshu",
    version="1.0",
    description="Smart Student Registration System",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "run.py", 
            base=base,
            target_name="Chakshu.exe",
            icon="static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
        )
    ]
) 