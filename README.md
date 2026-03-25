# pps project
quiz application

## Team Members
- Member 1: Core Engine
- Member 2: Data & Admin 
- Member 3: Analytics
- Member 4: GUI

## How to Run
Run main.py

## Project Structure
quiz_app/
├── data/
│ ├── questions.json    # Question bank
│ ├── admin_pass.txt    # Encrypted admin password
│ └── student_history/  # Folder for storing results
├── modules/
│ ├── init.py
│ ├── question_manager.py    # Question loading/saving
│ ├── quiz_engine.py         # Quiz logic
│ ├── score_analyzer.py      # Score calculations
│ └── admin_tools.py         # Admin functions
├── gui/
│ ├── init.py
│ ├── main_window.py        # Main PyQt window
│ ├── quiz_window.py        # Quiz taking interface
│ ├── admin_window.py       # Admin interface
│ └── results_window.py     # Results display
├── utils/
│ ├── init.py
│ ├── exceptions.py     # Custom exceptions
│ └── validators.py     # Input validation
├── main.py             # Entry point
└── requirements.txt     # Dependencies