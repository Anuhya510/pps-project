# main_window.py
# Complete Quiz Application with Role-Based Login

import sys
import json
import shutil
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QStackedWidget, QTabWidget,
    QTextEdit, QFileDialog, QDialog, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

# Import from existing modules
from gui.admin_window import (
    AdminWindow,
    AdminToolsSimple,
    FileQuestionManager,
    LoginDialog
)
from gui.quiz_window import MainWithQuiz
from gui.results_window import ScoreAnalyzerGUI

# Define file paths - Use the same path as quiz_window
BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = BASE_DIR / "data" / "questions.json"
PASSWORD_FILE = Path.home() / ".admin_tools" / "admin_pw.txt"
RESULTS_FILE = BASE_DIR / "data" / "quiz_results.json"


class LoginScreen(QWidget):
    """Login screen with Student and Admin options"""
    
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.admin_tools = AdminToolsSimple(FileQuestionManager(QUESTIONS_FILE), PASSWORD_FILE)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel("Quiz Application System")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Welcome. Please select your role.")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 40px;")
        layout.addWidget(subtitle)

        # Buttons container
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        # Student Button
        self.student_btn = QPushButton("Student")
        self.student_btn.setFont(QFont("Arial", 16))
        self.student_btn.setMinimumSize(200, 80)
        self.student_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.student_btn.clicked.connect(self.student_login)

        # Admin Button
        self.admin_btn = QPushButton("Administrator")
        self.admin_btn.setFont(QFont("Arial", 16))
        self.admin_btn.setMinimumSize(200, 80)
        self.admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 10px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.admin_btn.clicked.connect(self.admin_login)

        button_layout.addWidget(self.student_btn)
        button_layout.addWidget(self.admin_btn)
        button_container.setLayout(button_layout)
        layout.addWidget(button_container, alignment=Qt.AlignCenter)

        # Footer
        footer = QLabel("Student: Start quiz immediately | Administrator: Manage questions (password required)")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #95a5a6; margin-top: 40px;")
        layout.addWidget(footer)

        self.setLayout(layout)

    def student_login(self):
        """Handle student login - direct access to quiz"""
        self.on_login_success("student")

    def admin_login(self):
        """Handle admin login - show password dialog"""
        password, ok = QInputDialog.getText(
            self, "Admin Login", "Enter admin password:", QLineEdit.Password
        )
        
        if ok and self.admin_tools.verify_password(password):
            self.on_login_success("admin")
        elif ok:
            QMessageBox.warning(self, "Login Failed", "Incorrect password!")


class MainApplication(QMainWindow):
    """Main application window with role-based dashboards"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz Application System")
        self.setGeometry(100, 100, 1200, 700)
        
        self.current_role = None
        self.main_content = None
        
        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Add login screen
        self.login_screen = LoginScreen(self.on_login_success)
        self.stacked_widget.addWidget(self.login_screen)

    def logout(self):
        """Return to login screen"""
        # Confirm logout
        reply = QMessageBox.question(
            self, 
            "Confirm Logout", 
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Remove the current main content
        if self.main_content:
            self.stacked_widget.removeWidget(self.main_content)
            self.main_content.deleteLater()
            self.main_content = None
        
        # Go back to login screen
        self.stacked_widget.setCurrentWidget(self.login_screen)
        self.setWindowTitle("Quiz Application System")
        self.current_role = None

    def on_login_success(self, role):
        """Called after successful login"""
        self.current_role = role
        
        if role == "student":
            self.setup_student_mode()
        else:
            self.setup_admin_mode()
        
        self.stacked_widget.addWidget(self.main_content)
        self.stacked_widget.setCurrentWidget(self.main_content)
        self.setWindowTitle(f"Quiz Application - {role.title()} Mode")

    def setup_student_mode(self):
        """Student dashboard - only quiz and results"""
        self.main_content = QWidget()
        layout = QVBoxLayout(self.main_content)
        
        # Header with Logout button
        header_layout = QHBoxLayout()
        banner = QLabel("Student Dashboard")
        banner.setFont(QFont("Arial", 18, QFont.Bold))
        banner.setStyleSheet("color: #27ae60; padding: 10px;")
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        
        header_layout.addWidget(banner)
        header_layout.addStretch()
        header_layout.addWidget(logout_btn)
        layout.addLayout(header_layout)
        
        # Tabs - Student only gets Quiz and Results
        tabs = QTabWidget()
        tabs.addTab(MainWithQuiz(), "Take Quiz")
        tabs.addTab(self.create_results_tab(), "My Results")
        
        layout.addWidget(tabs)

    def setup_admin_mode(self):
        """Admin dashboard - question management and analytics only (no quiz)"""
        self.main_content = QWidget()
        layout = QVBoxLayout(self.main_content)
        
        # Header with Logout button
        header_layout = QHBoxLayout()
        banner = QLabel("Administrator Dashboard")
        banner.setFont(QFont("Arial", 18, QFont.Bold))
        banner.setStyleSheet("color: #2980b9; padding: 10px;")
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        
        header_layout.addWidget(banner)
        header_layout.addStretch()
        header_layout.addWidget(logout_btn)
        layout.addLayout(header_layout)
        
        # Initialize admin tools with correct path
        qm = FileQuestionManager(QUESTIONS_FILE)
        admin_tools = AdminToolsSimple(qm, PASSWORD_FILE)
        
        # Tabs - Admin only gets Manage Questions and Score Analyzer
        tabs = QTabWidget()
        tabs.addTab(AdminWindow(admin_tools), "Manage Questions")
        tabs.addTab(ScoreAnalyzerGUI(), "Score Analyzer")
        
        layout.addWidget(tabs)

    def create_results_tab(self):
        """Create results display tab for students"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        export_btn = QPushButton("Export Results")
        
        refresh_btn.clicked.connect(self.load_results)
        export_btn.clicked.connect(self.export_results)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        
        self.load_results()
        return widget

    def load_results(self):
        """Load and display quiz results"""
        if not RESULTS_FILE.exists():
            self.results_text.setText("No quiz results found. Please take a quiz to see results.")
            return
        
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as file:
                results = json.load(file)
            
            if not results:
                self.results_text.setText("No quiz results available.")
                return
            
            display_text = "<h3>Quiz History</h3><hr>"
            
            if isinstance(results, list):
                for index, quiz in enumerate(reversed(results[-10:]), 1):
                    student_name = quiz.get('student_name', 'Unknown')
                    display_text += f"""
                    <b>Quiz #{index}</b><br>
                    Student: {student_name}<br>
                    Date: {quiz.get('date', 'Unknown')}<br>
                    Score: {quiz.get('score', 0)} / {quiz.get('total', 0)}<br>
                    Percentage: {quiz.get('percentage', 0)}%<br>
                    <hr>
                    """
            else:
                display_text += f"""
                Score: {results.get('score', 0)} / {results.get('total', 0)}<br>
                Percentage: {results.get('percentage', 0)}%<br>
                """
            
            self.results_text.setHtml(display_text)
            
        except Exception as error:
            self.results_text.setText(f"Error loading results: {str(error)}")

    def export_results(self):
        """Export results to JSON file"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "quiz_results.json", "JSON Files (*.json)"
        )
        
        if filepath and RESULTS_FILE.exists():
            shutil.copy(RESULTS_FILE, filepath)
            QMessageBox.information(self, "Success", "Results exported successfully.")
        elif filepath:
            QMessageBox.warning(self, "Error", "No results available to export.")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainApplication()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()