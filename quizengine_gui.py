# quiz_gui.py
import sys
from pathlib import Path
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QLineEdit, QMessageBox, QComboBox, QListWidgetItem,
    QGroupBox, QRadioButton, QButtonGroup, QProgressBar, QDialog, QSpinBox
)
from PyQt5.QtCore import Qt

from question_manager import QuestionManager
from quiz_engine import QuizEngine  # adjust if filename differs

DATA_FILE = Path("data/questions.json")


class QuizWindow(QDialog):
    def __init__(self, qm: QuestionManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quiz")
        self.resize(700, 500)
        self.qm = qm
        self.engine: QuizEngine = None
        self.current_question: Dict[str, Any] = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)

        # Top controls: distribution selection and start button
        ctrl_row = QHBoxLayout()
        self.dist_easy = QSpinBox(); self.dist_easy.setRange(0, 50); self.dist_easy.setValue(3)
        self.dist_medium = QSpinBox(); self.dist_medium.setRange(0, 50); self.dist_medium.setValue(3)
        self.dist_hard = QSpinBox(); self.dist_hard.setRange(0, 50); self.dist_hard.setValue(4)
        self.start_btn = QPushButton("Start Quiz")
        self.start_btn.clicked.connect(self.start_quiz)

        ctrl_row.addWidget(QLabel("Easy:")); ctrl_row.addWidget(self.dist_easy)
        ctrl_row.addWidget(QLabel("Medium:")); ctrl_row.addWidget(self.dist_medium)
        ctrl_row.addWidget(QLabel("Hard:")); ctrl_row.addWidget(self.dist_hard)
        ctrl_row.addWidget(self.start_btn)

        main.addLayout(ctrl_row)

        # Question area
        self.question_label = QLabel("Press 'Start Quiz' to begin.")
        self.question_label.setWordWrap(True)
        self.options_group = QButtonGroup(self)
        self.options_box = QVBoxLayout()
        opt_container = QGroupBox("Options")
        opt_container.setLayout(self.options_box)

        main.addWidget(self.question_label)
        main.addWidget(opt_container)

        # Submit / Next / Quit
        action_row = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Answer")
        self.submit_btn.clicked.connect(self.submit_answer)
        self.submit_btn.setDisabled(True)
        self.next_btn = QPushButton("Next")
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
        self.progress = QProgressBar(); self.progress.setValue(0)
        self.score_label = QLabel("Score: 0")
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.score_label)
        main.addLayout(progress_row)

    def start_quiz(self):
        # Build flat question list and instantiate engine
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

        # initialize UI state
        self.progress.setMaximum(len(self.engine.selected_questions))
        self.progress.setValue(0)
        self.score_label.setText("Score: 0")
        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        self._show_current_question()

    def _clear_options(self):
        # Remove old radio buttons
        for btn in self.options_group.buttons():
            self.options_group.removeButton(btn)
            btn.deleteLater()

    def _show_current_question(self):
        try:
            question = self.engine.get_next_question()
        except IndexError:
            # No more questions -> show results
            self._show_results()
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.current_question = question
        self.question_label.setText(f"{self.engine.current_index + 1}. {question.get('question')}")
        # Build options as radio buttons
        self._clear_options()
        for i, opt in enumerate(question.get("options", [])):
            rb = QRadioButton(f"{i}. {opt}")
            self.options_group.addButton(rb, i)
            self.options_box.addWidget(rb)

        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)

    def submit_answer(self):
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

        # Show feedback and explanation
        explanation = self.engine.user_answers[-1].get("explanation", "")
        correct_option = self.engine.user_answers[-1].get("correct_option")
        msg = "Correct!" if is_correct else f"Incorrect. Correct: {correct_option}"
        if explanation:
            msg += f"\n\nExplanation:\n{explanation}"

        QMessageBox.information(self, "Result", msg)

        # Disable submit, enable next (or auto-advance if last)
        self.submit_btn.setEnabled(False)
        if self.engine.has_next_question():
            self.next_btn.setEnabled(True)
        else:
            self._show_results()

    def next_question(self):
        # Show next question. get_next_question returns current index question,
        # but engine.get_next_question doesn't advance, so call it directly.
        try:
            self._show_current_question()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _show_results(self):
        results = self.engine.get_results()
        summary = results["summary"]
        answers = results["answers"]

        text = (
            f"Quiz complete!\n\nScore: {summary['score']} / {summary['total_questions']}\n"
            f"Percentage: {summary['percentage']}%\n\nDetailed answers:\n"
        )
        for a in answers:
            text += (
                f"QID {a.get('question_id')}: {a.get('question')[:60]}...\n"
                f"Selected: {a.get('selected_option')}\n"
                f"Correct: {a.get('correct_option')}\n"
                f"{'Correct' if a.get('is_correct') else 'Incorrect'}\n\n"
            )

        QMessageBox.information(self, "Results", text)
        # After results, disable controls
        self.submit_btn.setDisabled(True)
        self.next_btn.setDisabled(True)

        # Optionally close dialog or let user close manually
        # self.accept()


class MainWithQuiz(QWidget):
    """
    Combines the QuestionManager list/editor with a Quiz starter.
    Reuses parts from the previous GUI but minimal: list on left, details on right, Start Quiz button.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Question Bank + Quiz")
        self.resize(1000, 600)
        self.qm = QuestionManager(DATA_FILE)
        self._build_ui()
        self._load_questions()

    def _build_ui(self):
        main = QHBoxLayout(self)

        # Left: question list and controls (reuse simplified listing)
        left = QVBoxLayout()
        top_row = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All")
        self.filter_combo.addItems(["easy", "medium", "hard"])
        self.filter_combo.currentIndexChanged.connect(self._load_questions)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self._load_questions)
        top_row.addWidget(QLabel("Filter:")); top_row.addWidget(self.filter_combo); top_row.addWidget(self.search_input)

        self.list_widget = QListWidget(); self.list_widget.itemClicked.connect(self._display_selected)

        left.addLayout(top_row)
        left.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.start_quiz_btn = QPushButton("Start Quiz")
        self.start_quiz_btn.clicked.connect(self.open_quiz_window)
        self.refresh_btn = QPushButton("Refresh"); self.refresh_btn.clicked.connect(self._load_questions)
        btn_row.addWidget(self.start_quiz_btn); btn_row.addWidget(self.refresh_btn)
        left.addLayout(btn_row)

        # Right: details
        right = QVBoxLayout()
        self.detail_label = QLabel("Select a question to see details.")
        self.detail_label.setWordWrap(True)
        right.addWidget(self.detail_label)

        main.addLayout(left, 3)
        main.addLayout(right, 5)

    def _load_questions(self):
        self.list_widget.clear()
        try:
            data = self.qm.get_all_questions()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
            return

        selected_filter = self.filter_combo.currentText().lower()
        query = self.search_input.text().strip().lower()

        items = []
        if selected_filter == "all":
            for diff, qs in data.items():
                items.extend(qs)
        else:
            items = data.get(selected_filter, [])

        if query:
            items = [
                q for q in items
                if query in q.get("question", "").lower()
                or query in q.get("topic", "").lower()
                or any(query in (opt or "").lower() for opt in q.get("options", []))
            ]

        for q in sorted(items, key=lambda x: x.get("id", 0)):
            text = f"[{q.get('id')}] ({q.get('difficulty')}) {q.get('question')[:80]}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, q)
            self.list_widget.addItem(item)

    def _display_selected(self, item: QListWidgetItem):
        q = item.data(Qt.UserRole)
        if not q:
            self.detail_label.setText("No details.")
            return
        details = []
        details.append(f"<b>ID:</b> {q.get('id')}")
        details.append(f"<b>Difficulty:</b> {q.get('difficulty')}")
        details.append(f"<b>Topic:</b> {q.get('topic', 'Unknown')}")
        details.append(f"<b>Question:</b> {q.get('question')}")
        opts = q.get("options", [])
        if opts:
            details.append("<b>Options:</b>")
            for i, o in enumerate(opts):
                marker = " (correct)" if i == q.get("correct") else ""
                details.append(f"{i}. {o}{marker}")
        if q.get("explanation"):
            details.append(f"<b>Explanation:</b> {q.get('explanation')}")
        self.detail_label.setText("<br>".join(details))

    def open_quiz_window(self):
        quiz_win = QuizWindow(self.qm, parent=self)
        quiz_win.exec_()


def main():
    app = QApplication(sys.argv)
    win = MainWithQuiz()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
