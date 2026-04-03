import sys
import json
from typing import List, Any, Dict, Optional

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QMessageBox, QListWidget, QComboBox, QSpinBox,
    QFormLayout, QGroupBox, QListWidgetItem
)
from PyQt5.QtCore import Qt

# Import your validation functions and exceptions
from validators import (
    validate_student_name,
    validate_question_data,
    validate_quiz_settings,
    validate_answer_choice
)
from utils.exceptions import (
    InvalidStudentError,
    InvalidQuestionError,
    InvalidQuizSettingsError
)


class StudentWidget(QGroupBox):
    def __init__(self):
        super().__init__("Student")
        layout = QFormLayout()
        self.name_input = QLineEdit()
        layout.addRow("Student Name:", self.name_input)
        self.validate_btn = QPushButton("Validate Name")
        self.validate_btn.clicked.connect(self.on_validate)
        layout.addRow(self.validate_btn)
        self.setLayout(layout)

    def on_validate(self):
        name = self.name_input.text()
        try:
            validate_student_name(name)
            QMessageBox.information(self, "OK", "Student name is valid.")
        except InvalidStudentError as e:
            QMessageBox.warning(self, "Invalid Student", str(e))


class QuestionWidget(QGroupBox):
    def __init__(self):
        super().__init__("Question")
        self.setLayout(QVBoxLayout())

        form = QFormLayout()
        self.id_input = QLineEdit()
        self.question_input = QTextEdit()
        self.options_input = QTextEdit()
        self.answer_input = QLineEdit()
        self.topic_input = QLineEdit()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard"])

        form.addRow("ID:", self.id_input)
        form.addRow("Question:", self.question_input)
        form.addRow("Options (one per line):", self.options_input)
        form.addRow("Correct Answer:", self.answer_input)
        form.addRow("Topic:", self.topic_input)
        form.addRow("Difficulty:", self.difficulty_combo)

        self.layout().addLayout(form)

        btn_layout = QHBoxLayout()
        self.validate_btn = QPushButton("Validate Question")
        self.validate_btn.clicked.connect(self.on_validate)
        self.add_to_bank_btn = QPushButton("Add to Bank")
        self.add_to_bank_btn.clicked.connect(self.on_add_to_bank)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.add_to_bank_btn)
        self.layout().addLayout(btn_layout)

    def _read_question(self) -> Dict[str, Any]:
        raw_options = [o.strip() for o in self.options_input.toPlainText().splitlines() if o.strip()]
        q = {
            "id": self.id_input.text().strip() or None,
            "question": self.question_input.toPlainText().strip(),
            "options": raw_options,
            "answer": self.answer_input.text().strip(),
            "topic": self.topic_input.text().strip(),
            "difficulty": self.difficulty_combo.currentText()
        }
        return q

    def on_validate(self):
        q = self._read_question()
        try:
            validate_question_data(q)
            QMessageBox.information(self, "OK", "Question is valid.")
        except InvalidQuestionError as e:
            QMessageBox.warning(self, "Invalid Question", str(e))

    def on_add_to_bank(self):
        q = self._read_question()
        try:
            validate_question_data(q)
        except InvalidQuestionError as e:
            QMessageBox.warning(self, "Invalid Question", str(e))
            return
        # Emit a signal or directly add to bank via parent reference; simple approach:
        self.parent().add_question_to_bank(q)


class QuizSettingsWidget(QGroupBox):
    def __init__(self):
        super().__init__("Quiz Settings")
        self.setLayout(QFormLayout())

        self.num_spin = QSpinBox()
        self.num_spin.setMinimum(1)
        self.num_spin.setMaximum(1000)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItem("")  # allow empty
        self.difficulty_combo.addItems(["easy", "medium", "hard"])
        self.topic_input = QLineEdit()

        self.validate_btn = QPushButton("Validate Settings")
        self.validate_btn.clicked.connect(self.on_validate)

        self.layout().addRow("Number of Questions:", self.num_spin)
        self.layout().addRow("Difficulty (optional):", self.difficulty_combo)
        self.layout().addRow("Topic (optional):", self.topic_input)
        self.layout().addRow(self.validate_btn)

    def on_validate(self):
        num = self.num_spin.value()
        diff = self.difficulty_combo.currentText() or None
        topic = self.topic_input.text().strip() or None
        try:
            validate_quiz_settings(num, diff, topic)
            QMessageBox.information(self, "OK", "Quiz settings are valid.")
        except InvalidQuizSettingsError as e:
            QMessageBox.warning(self, "Invalid Settings", str(e))


class QuestionBankWidget(QGroupBox):
    def __init__(self):
        super().__init__("Question Bank")
        self.setLayout(QVBoxLayout())
        self.list_widget = QListWidget()
        self.layout().addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load from JSON")
        self.load_btn.clicked.connect(self.load_from_json)
        self.export_btn = QPushButton("Export JSON")
        self.export_btn.clicked.connect(self.export_json)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.remove_btn)
        self.layout().addLayout(btn_layout)

        self.questions: List[Dict[str, Any]] = []

    def add_question(self, q: Dict[str, Any]):
        self.questions.append(q)
        item = QListWidgetItem(f"{q.get('id') or 'no-id'}: {q.get('question')[:60]}")
        item.setData(Qt.UserRole, q)
        self.list_widget.addItem(item)

    def add_from_list(self, qs: List[Dict[str, Any]]):
        for q in qs:
            try:
                validate_question_data(q)
                self.add_question(q)
            except InvalidQuestionError:
                continue

    def load_from_json(self):
        # Basic input dialog to paste JSON (no file dialog to keep simple)
        text, ok = QInputDialog.getMultiLineText(self, "Load Questions JSON",
                                                 "Paste JSON array of questions:")
        if not ok or not text.strip():
            return
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                self.add_from_list(parsed)
                QMessageBox.information(self, "Loaded", f"Loaded {len(parsed)} items (valid ones added).")
            else:
                QMessageBox.warning(self, "Invalid", "JSON must be an array of question objects.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to parse JSON: {e}")

    def export_json(self):
        if not self.questions:
            QMessageBox.information(self, "No Data", "No questions to export.")
            return
        text = json.dumps(self.questions, indent=2)
        # Show in a dialog to copy
        dlg = QTextEdit()
        dlg.setWindowTitle("Exported Questions JSON")
        dlg.setReadOnly(True)
        dlg.setPlainText(text)
        dlg.setMinimumSize(600, 400)
        dlg.show()
        # Keep reference so it doesn't get garbage-collected
        self._export_dialog = dlg

    def remove_selected(self):
        sel = self.list_widget.currentItem()
        if not sel:
            return
        q = sel.data(Qt.UserRole)
        idx = self.list_widget.row(sel)
        self.list_widget.takeItem(idx)
        try:
            self.questions.remove(q)
        except ValueError:
            pass


class AnswerValidationWidget(QGroupBox):
    def __init__(self):
        super().__init__("Answer Validation")
        self.setLayout(QFormLayout())
        self.options_input = QTextEdit()
        self.choice_input = QLineEdit()
        self.validate_btn = QPushButton("Validate Choice")
        self.validate_btn.clicked.connect(self.on_validate)
        self.layout().addRow("Options (one per line):", self.options_input)
        self.layout().addRow("Selected Choice:", self.choice_input)
        self.layout().addRow(self.validate_btn)

    def on_validate(self):
        options = [o.strip() for o in self.options_input.toPlainText().splitlines() if o.strip()]
        choice = self.choice_input.text().strip()
        try:
            validate_answer_choice(choice, options)
            QMessageBox.information(self, "OK", "Selected answer is valid.")
        except InvalidQuestionError as e:
            QMessageBox.warning(self, "Invalid Choice", str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz Validator GUI")
        self.resize(1000, 700)

        main_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        # Left column widgets
        self.student_widget = StudentWidget()
        self.question_widget = QuestionWidget()
        left_col.addWidget(self.student_widget)
        left_col.addWidget(self.question_widget)

        # Right column widgets
        self.settings_widget = QuizSettingsWidget()
        self.bank_widget = QuestionBankWidget()
        self.answer_widget = AnswerValidationWidget()
        right_col.addWidget(self.settings_widget)
        right_col.addWidget(self.bank_widget)
        right_col.addWidget(self.answer_widget)

        main_layout.addLayout(left_col, 2)
        main_layout.addLayout(right_col, 3)

        # Top-level buttons
        btn_layout = QHBoxLayout()
        self.run_quiz_btn = QPushButton("Run Quick Demo")
        self.run_quiz_btn.clicked.connect(self.run_quiz_demo)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_quiz_btn)

        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_layout)
        outer_layout.addLayout(btn_layout)

        self.setLayout(outer_layout)

        # Allow child widgets to call back
        self.question_widget.setParent(self)
        self.bank_widget.setParent(self)

    def add_question_to_bank(self, q: Dict[str, Any]):
        self.bank_widget.add_question(q)
        QMessageBox.information(self, "Added", "Question added to bank.")

    def run_quiz_demo(self):
        # Simple demo: attempt to validate settings and pick first question to answer
        try:
            num = self.settings_widget.num_spin.value()
            diff = self.settings_widget.difficulty_combo.currentText() or None
            topic = self.settings_widget.topic_input.text().strip() or None
            validate_quiz_settings(num, diff, topic)
        except InvalidQuizSettingsError as e:
            QMessageBox.warning(self, "Invalid Settings", str(e))
            return

        if not self.bank_widget.questions:
            QMessageBox.information(self, "No Questions", "Add at least one question to the bank first.")
            return

        # Pick first valid question matching optional filters
        selected = None
        for q in self.bank_widget.questions:
            if diff and q.get("difficulty", "").lower() != diff.lower():
                continue
            if topic and q.get("topic", "").lower() != topic.lower():
                continue
            selected = q
            break

        if not selected:
            QMessageBox.information(self, "No Match", "No question in bank matches the selected filters.")
            return

        # Show question and options in dialog and let user pick
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Quiz Demo")
        question_text = selected.get("question", "")
        options = selected.get("options", [])
        dlg.setText(question_text)
        # Add buttons for each option
        for opt in options:
            dlg.addButton(opt, QMessageBox.ActionRole)
        dlg.addButton("Cancel", QMessageBox.RejectRole)
        clicked = dlg.exec_()
        # QMessageBox doesn't return which action; instead use custom dialog below for better behavior
        # To keep simple, show options in a list selection dialog

        sel_dlg = OptionSelectDialog(question_text, options, parent=self)
        if sel_dlg.exec_():
            choice = sel_dlg.selected_option
            try:
                validate_answer_choice(choice, options)
                is_correct = choice == selected.get("answer")
                if is_correct:
                    QMessageBox.information(self, "Result", "Correct!")
                else:
                    QMessageBox.information(self, "Result", f"Incorrect. Correct answer: {selected.get('answer')}")
            except InvalidQuestionError as e:
                QMessageBox.warning(self, "Invalid Choice", str(e))


from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QInputDialog, QListView


class OptionSelectDialog(QDialog):
    def __init__(self, question: str, options: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Answer")
        self.selected_option: Optional[str] = None
        self.setLayout(QVBoxLayout())
        lbl = QLabel(question)
        lbl.setWordWrap(True)
        self.layout().addWidget(lbl)

        self.list_widget = QListWidget()
        for o in options:
            self.list_widget.addItem(o)
        self.layout().addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)

    def on_accept(self):
        sel = self.list_widget.currentItem()
        if not sel:
            QMessageBox.warning(self, "No Selection", "Please choose an option.")
            return
        self.selected_option = sel.text()
        self.accept()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
