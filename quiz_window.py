# quiz_window.py
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(_file_).resolve().parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QGroupBox, QRadioButton, QButtonGroup,
    QProgressBar, QDialog, QSpinBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import from modules
from modules.question_manager import QuestionManager
from modules.quiz_engine import QuizEngine

BASE_DIR = Path(_file_).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "questions.json"


class QuizWindow(QDialog):
    """Quiz taking window - appears when Start Quiz is clicked"""
    
    def _init_(self, qm: QuestionManager, parent=None):
        super()._init_(parent)
        self.setWindowTitle("Take Quiz")
        self.resize(700, 500)
        self.qm = qm
        self.engine: QuizEngine = None
        self.current_question: Dict[str, Any] = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Top controls: distribution selection and start button
        ctrl_row = QHBoxLayout()
        self.dist_easy = QSpinBox()
        self.dist_easy.setRange(0, 50)
        self.dist_easy.setValue(3)
        self.dist_medium = QSpinBox()
        self.dist_medium.setRange(0, 50)
        self.dist_medium.setValue(3)
        self.dist_hard = QSpinBox()
        self.dist_hard.setRange(0, 50)
        self.dist_hard.setValue(4)
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.clicked.connect(self.start_quiz)

        ctrl_row.addWidget(QLabel("Easy:"))
        ctrl_row.addWidget(self.dist_easy)
        ctrl_row.addWidget(QLabel("Medium:"))
        ctrl_row.addWidget(self.dist_medium)
        ctrl_row.addWidget(QLabel("Hard:"))
        ctrl_row.addWidget(self.dist_hard)
        ctrl_row.addWidget(self.start_btn)

        main.addLayout(ctrl_row)

        # Question area
        self.question_label = QLabel("Press 'Start Quiz' to begin.")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        
        self.options_group = QButtonGroup(self)
        self.options_box = QVBoxLayout()
        opt_container = QGroupBox("Select your answer")
        opt_container.setLayout(self.options_box)

        main.addWidget(self.question_label)
        main.addWidget(opt_container)

        # Submit / Next / Quit
        action_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Answer")
        self.submit_btn.clicked.connect(self.submit_answer)
        self.submit_btn.setDisabled(True)
        self.next_btn = QPushButton("Next Question")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setDisabled(True)
        self.quit_btn = QPushButton("Quit")
        self.quit_btn.clicked.connect(self.reject)

        action_row.addWidget(self.submit_btn)
        action_row.addWidget(self.next_btn)
        action_row.addWidget(self.quit_btn)

        main.addLayout(action_row)

        # Progress and score
        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("font-weight: bold;")
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.score_label)
        main.addLayout(progress_row)

    def start_quiz(self):
        """Start the quiz with selected difficulty distribution"""
        questions = self.qm.get_all_questions_flat()
        if not questions:
            QMessageBox.warning(self, "No Questions", "No questions available to start quiz.")
            return

        distribution = {
            "easy": int(self.dist_easy.value()),
            "medium": int(self.dist_medium.value()),
            "hard": int(self.dist_hard.value())
        }

        try:
            self.engine = QuizEngine(questions)
            self.engine.generate_quiz(distribution=distribution)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate quiz: {e}")
            return

        # Initialize UI state
        self.progress.setMaximum(len(self.engine.selected_questions))
        self.progress.setValue(0)
        self.score_label.setText("Score: 0")
        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        
        # Disable distribution controls during quiz
        self.dist_easy.setEnabled(False)
        self.dist_medium.setEnabled(False)
        self.dist_hard.setEnabled(False)
        self.start_btn.setEnabled(False)
        
        self._show_current_question()

    def _clear_options(self):
        """Remove old radio buttons"""
        for btn in self.options_group.buttons():
            self.options_group.removeButton(btn)
            btn.deleteLater()

    def _show_current_question(self):
        """Display the current question and options"""
        try:
            question = self.engine.get_next_question()
        except IndexError:
            self._show_results()
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.current_question = question
        self.question_label.setText(f"Question {self.engine.current_index + 1}: {question.get('question')}")
        
        # Build options as radio buttons
        self._clear_options()
        for i, opt in enumerate(question.get("options", [])):
            rb = QRadioButton(f"{chr(65+i)}. {opt}")
            rb.setStyleSheet("padding: 5px;")
            self.options_group.addButton(rb, i)
            self.options_box.addWidget(rb)

        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)

    def submit_answer(self):
        """Submit the selected answer"""
        selected_id = self.options_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Select Answer", "Please select an option.")
            return

        try:
            is_correct = self.engine.submit_answer(selected_id)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        # Update score and progress
        self.score_label.setText(f"Score: {self.engine.get_score()}")
        self.progress.setValue(self.engine.current_index)

        # Show feedback
        correct_option = self.engine.user_answers[-1].get("correct_option")
        msg = "Correct!" if is_correct else f"Incorrect. Correct answer: {correct_option}"
        QMessageBox.information(self, "Result", msg)

        # Disable submit, enable next
        self.submit_btn.setEnabled(False)
        if self.engine.has_next_question():
            self.next_btn.setEnabled(True)
        else:
            self._show_results()

    def next_question(self):
        """Move to next question"""
        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        self._show_current_question()

    def _show_results(self):
        """Display quiz results in a scrollable dialog"""
        results = self.engine.get_results()
        summary = results["summary"]
        answers = results["answers"]
        
        # Save results to file
        self._save_results(results)
        
        # Create a scrollable results dialog
        results_dialog = QDialog(self)
        results_dialog.setWindowTitle("Quiz Results")
        results_dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(results_dialog)
        
        # Score summary at top
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 10px;")
        summary_layout = QVBoxLayout(summary_frame)
        
        score_label = QLabel(f"SCORE: {summary['score']} / {summary['total_questions']}")
        score_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        score_label.setAlignment(Qt.AlignCenter)
        
        percent_color = "#27ae60" if summary['percentage'] >= 60 else "#e74c3c"
        percent_label = QLabel(f"Percentage: {summary['percentage']}%")
        percent_label.setStyleSheet(f"font-size: 14px; color: {percent_color};")
        percent_label.setAlignment(Qt.AlignCenter)
        
        summary_layout.addWidget(score_label)
        summary_layout.addWidget(percent_label)
        layout.addWidget(summary_frame)
        
        # Scroll area for detailed answers
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        
        # Add each answer
        for idx, answer in enumerate(answers, 1):
            q_frame = QFrame()
            q_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
            q_frame.setStyleSheet("background-color: white; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px;")
            q_layout = QVBoxLayout(q_frame)
            
            status_color = "#27ae60" if answer.get('is_correct') else "#e74c3c"
            status_text = "CORRECT" if answer.get('is_correct') else "INCORRECT"
            
            header = QLabel(f"{idx}. {status_text} - {answer.get('question', '')[:100]}")
            header.setStyleSheet(f"font-weight: bold; color: {status_color};")
            header.setWordWrap(True)
            q_layout.addWidget(header)
            
            selected = QLabel(f"Your answer: {answer.get('selected_option', 'N/A')}")
            selected.setStyleSheet("color: #555; margin-left: 10px;")
            selected.setWordWrap(True)
            q_layout.addWidget(selected)
            
            if not answer.get('is_correct'):
                correct = QLabel(f"Correct answer: {answer.get('correct_option', 'N/A')}")
                correct.setStyleSheet("color: #27ae60; margin-left: 10px;")
                correct.setWordWrap(True)
                q_layout.addWidget(correct)
            
            if answer.get('explanation'):
                explanation = QLabel(f"Explanation: {answer.get('explanation', '')}")
                explanation.setStyleSheet("color: #7f8c8d; font-style: italic; margin-left: 10px; margin-top: 5px;")
                explanation.setWordWrap(True)
                q_layout.addWidget(explanation)
            
            content_layout.addWidget(q_frame)
        
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #2980b9; color: white; padding: 8px; border-radius: 5px;")
        close_btn.clicked.connect(results_dialog.accept)
        layout.addWidget(close_btn)
        
        results_dialog.exec_()
        
        # Disable quiz controls
        self.submit_btn.setDisabled(True)
        self.next_btn.setDisabled(True)
        
        # Close the quiz window
        self.accept()

    def _save_results(self, results):
        """Save quiz results to JSON file for later analysis"""
        try:
            results_dir = BASE_DIR / "data"
            results_dir.mkdir(exist_ok=True)
            results_file = results_dir / "quiz_results.json"
            
            result_data = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": results["summary"]["score"],
                "total": results["summary"]["total_questions"],
                "percentage": results["summary"]["percentage"],
                "answers": results["answers"]
            }
            
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                    if isinstance(existing_results, list):
                        existing_results.append(result_data)
                    else:
                        existing_results = [existing_results, result_data]
            else:
                existing_results = [result_data]
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving results: {e}")


class MainWithQuiz(QWidget):
    """
    Simplified quiz interface - only shows quiz taking controls.
    No question list displayed for cleaner student experience.
    """
    def _init_(self):
        super()._init_()
        self.setWindowTitle("Take Quiz")
        self.resize(700, 500)
        self.qm = QuestionManager(DATA_FILE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Take a Quiz")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2980b9; margin: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Select difficulty distribution and click Start Quiz to begin")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # Quiz settings group
        settings_group = QGroupBox("Quiz Settings")
        settings_layout = QHBoxLayout()
        
        self.easy_spin = QSpinBox()
        self.easy_spin.setRange(0, 20)
        self.easy_spin.setValue(3)
        self.medium_spin = QSpinBox()
        self.medium_spin.setRange(0, 20)
        self.medium_spin.setValue(3)
        self.hard_spin = QSpinBox()
        self.hard_spin.setRange(0, 20)
        self.hard_spin.setValue(4)
        
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.setStyleSheet("background-color: #27ae60; padding: 10px; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_quiz)
        
        settings_layout.addWidget(QLabel("Easy:"))
        settings_layout.addWidget(self.easy_spin)
        settings_layout.addWidget(QLabel("Medium:"))
        settings_layout.addWidget(self.medium_spin)
        settings_layout.addWidget(QLabel("Hard:"))
        settings_layout.addWidget(self.hard_spin)
        settings_layout.addStretch()
        settings_layout.addWidget(self.start_btn)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Info label
        self.info_label = QLabel("Select number of questions per difficulty level, then click Start Quiz")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #555; margin-top: 20px;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()

    def start_quiz(self):
        """Open the quiz window with selected settings"""
        # Create quiz window and pass question manager
        quiz_win = QuizWindow(self.qm, parent=self)
        
        # Set the distribution values in quiz window
        quiz_win.dist_easy.setValue(self.easy_spin.value())
        quiz_win.dist_medium.setValue(self.medium_spin.value())
        quiz_win.dist_hard.setValue(self.hard_spin.value())
        
        # Start the quiz automatically
        quiz_win.start_quiz()
        
        # Show the quiz window
        quiz_win.exec_()


def main():
    app = QApplication(sys.argv)
    win = MainWithQuiz()
    win.show()
    sys.exit(app.exec_())


if _name_ == "_main_":
    main()
