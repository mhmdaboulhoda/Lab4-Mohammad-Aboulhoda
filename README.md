# Lab4-Mohammad-Aboulhoda
A project combining Tkinter and PyQt documented implementations

# School Management System – Tkinter & PyQt

This project demonstrates a **School Management System** with two graphical user interfaces (GUIs):  
- One implemented using **Tkinter** (standard Python GUI toolkit).  
- Another implemented using **PyQt5** (powerful cross-platform framework).  

The system is fully backed by:  
- **SQLite database (`school.db`)** for persistent storage.  
- **JSON serialization** for easy import/export of data.  
- **Object-oriented class models** (`Student`, `Instructor`, `Course`) that manage relationships.  

---

## Features

### 1. Core Entities
- **Students**: Can be added with ID, name, age, and email.  
- **Instructors**: Can be assigned courses.  
- **Courses**: Support instructor assignment and student registration.  

### 2. GUI Options
- **Tkinter UI (`gui_tkinter.py`)**  
  - Forms to add students, instructors, and courses.  
  - Tabs for **Forms** and **Records & Search**.  
  - Scrollable lists with add/edit/delete actions.  
  - Database save/load/backup options.  

- **PyQt5 UI (`gui_pyqt.py`)**  
  - Modern interface with tabbed layout.  
  - Dialog windows for editing students, instructors, and courses.  
  - Export data to **CSV** (students.csv, instructors.csv, courses.csv).  
  - Integration with SQLite for database persistence.  

### 3. Data Storage
- **SQLite (`db.py`)**  
  - Tables for `students`, `instructors`, `courses`, and `registrations` (many-to-many).  
  - Functions for initialization, saving all objects, and loading back into memory.  

- **JSON (`datastore.py`)**  
  - Save and load full project state to JSON files.  
  - Restores relationships (student-course registrations, instructor-course assignments).  

### 4. Web Extension
- A simple **Flask app (`hello.py`)** is included as a starting point for a future web interface.  

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/mhmdaboulhoda/Lab4-Mohammad-Aboulhoda.git
   cd Lab4-Mohammad-Aboulhoda

# macOS
python3.11 -m venv .venv
source .venv/bin/activate

# Windows
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

## Install dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install PyQt5 Flask

## Project structure
.
├── classes.py        # Core domain models: Student, Instructor, Course
├── datastore.py      # JSON save/load (export/import all entities & relations)
├── db.py             # SQLite schema + helpers (init_db, save_all, load_all, backup_to)
├── gui_tkinter.py    # Tkinter GUI (forms, lists, add/edit/delete, save/load)
├── gui_pyqt.py       # PyQt5 GUI (tabbed UI, dialogs, CSV export, DB integration)
├── hello.py          # Minimal Flask "hello" app (future web extension)
└── README.md

