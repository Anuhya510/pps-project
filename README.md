# PPS PROJECT- QUIZ APPLICATION  

A Python-based quiz application with GUI support for conducting quizzes, managing questions, and tracking student performance.

## Team Members
- Member 1: Core Engine
- Member 2: Data & Admin 
- Member 3: Analytics
- Member 4: GUI

## Requirements
- Python 3.x

Install dependencies:
```bash
pip install -r requirements.txt

## How to Run
Run main.py

## Project Structure
```text
quiz_app/
│
├── data/
│   ├── questions.json          # Central question bank
│   ├── admin_pass.txt          # Encrypted admin password
│   └── student_history/        # Stored quiz results per student
│
├── modules/
│   ├── __init__.py
│   ├── question_manager.py     # CRUD operations & question handling
│   ├── quiz_engine.py          # Core quiz logic
│   ├── score_analyzer.py       # Score calculation & analytics
│   └── admin_tools.py          # Admin workflows & validation layer
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # Main PyQt application window
│   ├── quiz_window.py          # Quiz-taking interface
│   ├── admin_window.py         # Admin control panel
│   └── results_window.py       # Results & feedback display
│
├── utils/
│   ├── __init__.py
│   ├── exceptions.py           # Custom exception definitions
│   └── validators.py           # Input & data validation utilities
│
├── main.py                     # Application entry point
└── requirements.txt            # Project dependencies
```
