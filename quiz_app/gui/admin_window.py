# admin_window.py
import sys
from pathlib import Path
from typing import Dict, Any, List
import json

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QTextEdit, QMessageBox, QComboBox, QFormLayout, QDialog, QInputDialog,
    QFileDialog, QButtonGroup, QRadioButton
)

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import modules
from modules.question_manager import QuestionManager
from modules.quiz_engine import QuizEngine

# Define correct path for questions
BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"

from hashlib import sha256


class FileQuestionManager:
    """Manages questions with JSON file storage - uses same path as quiz"""
    
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])
        self._load()

    def _load(self):
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both list and dictionary formats
            if isinstance(data, list):
                self._questions = data
            elif isinstance(data, dict):
                self._questions = []
                for level in data.values():
                    if isinstance(level, list):
                        self._questions.extend(level)
            else:
                self._questions = []
        
        self._by_id = {q["id"]: q for q in self._questions if "id" in q}
        self._next_id = max((q["id"] for q in self._questions), default=0) + 1

    def _write(self, data):
        # Save as list format (flat)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_next_id(self):
        """Generate unique ID across all questions."""
        return self._next_id

    def add_question(self, question, options, correct, difficulty, topic, explanation=""):
        """Add a new question with unique ID."""
        q = {
            "id": self._get_next_id(),
            "question": question,
            "options": options,
            "correct": correct,
            "difficulty": difficulty,
            "topic": topic,
            "explanation": explanation
        }
        self._next_id += 1
        self._questions.append(q)
        self._by_id[q["id"]] = q
        self._write(self._questions)
        return q

    def edit_question(self, question_id, updates):
        q = self._by_id.get(question_id)
        if not q:
            return False
        for k, v in updates.items():
            if k == "id":
                continue
            q[k] = v
        self._write(self._questions)
        return True

    def delete_question(self, question_id):
        q = self._by_id.pop(question_id, None)
        if not q:
            return False
        self._questions = [x for x in self._questions if x["id"] != question_id]
        self._write(self._questions)
        return True

    def get_all_questions_flat(self):
        return list(self._questions)

    def get_all_questions(self):
        """Return questions categorized by difficulty."""
        categorized = {"easy": [], "medium": [], "hard": []}
        for q in self._questions:
            diff = q.get("difficulty", "medium")
            if diff in categorized:
                categorized[diff].append(q)
        return categorized

    def reset_all(self):
        self._questions = []
        self._by_id = {}
        self._next_id = 1
        self._write(self._questions)

    def backup(self):
        backup_path = self.path.with_suffix(".backup.json")
        with backup_path.open("w", encoding="utf-8") as f:
            json.dump(self._questions, f, indent=2, ensure_ascii=False)
        return backup_path

    def get_statistics(self):
        total = len(self._questions)
        difficulty = {}
        topics = {}
        for q in self._questions:
            diff = q.get("difficulty", "unknown")
            difficulty[diff] = difficulty.get(diff, 0) + 1
            topic = q.get("topic", "unknown")
            topics[topic] = topics.get(topic, 0) + 1
        return {"total": total, "difficulty": difficulty, "topics": topics}


class AdminToolsSimple:
    def __init__(self, qm, password_file: Path):
        self.qm = qm
        self.password_file = Path(password_file)
        self.password_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.password_file.exists():
            self._write_password("admin123")

    def _hash_password(self, password: str) -> str:
        return sha256(password.encode()).hexdigest()

    def _write_password(self, password: str):
        with self.password_file.open("w", encoding="utf-8") as f:
            f.write(self._hash_password(password))

    def verify_password(self, password: str) -> bool:
        if not self.password_file.exists():
            return False
        with self.password_file.open("r", encoding="utf-8") as f:
            stored = f.read().strip()
        return stored == self._hash_password(password)

    def change_password(self, old_password: str, new_password: str) -> bool:
        if not self.verify_password(old_password):
            return False
        self._write_password(new_password)
        return True

    def add_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.qm.add_question(
            question=data["question"],
            options=data["options"],
            correct=data["correct"],
            difficulty=data["difficulty"],
            topic=data["topic"],
            explanation=data.get("explanation", "")
        )

    def edit_question(self, question_id: int, updates: Dict[str, Any]) -> bool:
        return self.qm.edit_question(question_id, updates)

    def delete_question(self, question_id: int) -> bool:
        return self.qm.delete_question(question_id)

    def view_all_questions(self) -> List[Dict[str, Any]]:
        return self.qm.get_all_questions_flat()

    def reset_questions(self) -> None:
        self.qm.reset_all()

    def backup_questions(self) -> Path:
        return self.qm.backup()

    def get_statistics(self) -> Dict[str, Any]:
        return self.qm.get_statistics()


class LoginDialog(QDialog):
    def __init__(self, admin_tools: AdminToolsSimple):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.admin_tools = admin_tools
        self.resize(300, 100)

        layout = QFormLayout(self)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.password_edit)

        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.login_btn.clicked.connect(self.try_login)
        self.cancel_btn.clicked.connect(self.reject)

    def try_login(self):
        if self.admin_tools.verify_password(self.password_edit.text()):
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect password")


class QuestionEditorDialog(QDialog):
    def __init__(self, parent=None, question: Dict[str, Any]=None):
        super().__init__(parent)
        self.setWindowTitle("Question Editor")
        self.resize(600, 400)
        self.question = question

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.question_edit = QTextEdit()
        self.options_edit = QTextEdit()
        self.correct_combo = QComboBox()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard"])
        self.topic_edit = QLineEdit()
        self.explanation_edit = QTextEdit()

        form.addRow("Question:", self.question_edit)
        form.addRow("Options (one per line):", self.options_edit)
        form.addRow("Correct option (select):", self.correct_combo)
        form.addRow("Difficulty:", self.difficulty_combo)
        form.addRow("Topic:", self.topic_edit)
        form.addRow("Explanation:", self.explanation_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        if self.question:
            self._load_question()
        
        # Update correct options when options change
        self.options_edit.textChanged.connect(self._update_correct_options)

    def _update_correct_options(self):
        """Update the correct answer dropdown when options change."""
        options = [o.strip() for o in self.options_edit.toPlainText().splitlines() if o.strip()]
        self.correct_combo.clear()
        for i, opt in enumerate(options):
            self.correct_combo.addItem(f"{chr(65+i)}. {opt}", i)

    def _load_question(self):
        self.question_edit.setPlainText(self.question.get("question", ""))
        options = self.question.get("options", [])
        self.options_edit.setPlainText("\n".join(options))
        self._update_correct_options()
        
        correct_idx = self.question.get("correct", 0)
        if correct_idx < self.correct_combo.count():
            self.correct_combo.setCurrentIndex(correct_idx)
        
        diff = self.question.get("difficulty", "easy")
        idx = max(0, self.difficulty_combo.findText(diff))
        self.difficulty_combo.setCurrentIndex(idx)
        self.topic_edit.setText(self.question.get("topic", ""))
        self.explanation_edit.setPlainText(self.question.get("explanation", ""))

    def get_data(self):
        options = [o.strip() for o in self.options_edit.toPlainText().splitlines() if o.strip()]
        return {
            "question": self.question_edit.toPlainText().strip(),
            "options": options,
            "correct": self.correct_combo.currentIndex(),
            "difficulty": self.difficulty_combo.currentText(),
            "topic": self.topic_edit.text().strip(),
            "explanation": self.explanation_edit.toPlainText().strip()
        }


class AdminWindow(QWidget):
    def __init__(self, admin_tools: AdminToolsSimple):
        super().__init__()
        self.setWindowTitle("Admin Tools - Question Bank Management")
        self.resize(1000, 650)
        self.admin = admin_tools

        main_layout = QHBoxLayout(self)

        # Left: question list and actions
        left = QVBoxLayout()
        
        # Search and filter
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "easy", "medium", "hard"])
        self.filter_combo.currentTextChanged.connect(self.refresh_questions)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search questions...")
        self.search_input.textChanged.connect(self.refresh_questions)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(self.search_input)
        left.addLayout(filter_layout)
        
        self.list_widget = QListWidget()
        left.addWidget(QLabel(f"Questions ({self.admin.view_all_questions().__len__()} total)"))
        left.addWidget(self.list_widget)

        list_btns = QHBoxLayout()
        self.add_btn = QPushButton("Add Question")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        list_btns.addWidget(self.add_btn)
        list_btns.addWidget(self.edit_btn)
        list_btns.addWidget(self.delete_btn)
        left.addLayout(list_btns)

        main_layout.addLayout(left, 2)

        # Right: details and system actions
        right = QVBoxLayout()
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        right.addWidget(QLabel("Question Details"))
        right.addWidget(self.detail)

        sys_btns = QHBoxLayout()
        self.backup_btn = QPushButton("Backup")
        self.reset_btn = QPushButton("Reset All")
        self.stats_btn = QPushButton("Statistics")
        self.change_pw_btn = QPushButton("Change Password")
        sys_btns.addWidget(self.backup_btn)
        sys_btns.addWidget(self.reset_btn)
        sys_btns.addWidget(self.stats_btn)
        sys_btns.addWidget(self.change_pw_btn)
        right.addLayout(sys_btns)

        main_layout.addLayout(right, 3)

        # Connect signals
        self.add_btn.clicked.connect(self.add_question)
        self.edit_btn.clicked.connect(self.edit_question)
        self.delete_btn.clicked.connect(self.delete_question)
        self.list_widget.currentItemChanged.connect(self.show_details)
        self.backup_btn.clicked.connect(self.backup)
        self.reset_btn.clicked.connect(self.reset_all)
        self.stats_btn.clicked.connect(self.show_stats)
        self.change_pw_btn.clicked.connect(self.change_password)

        self.refresh_questions()

    def refresh_questions(self):
        self.list_widget.clear()
        all_questions = self.admin.view_all_questions()
        
        # Apply filters
        filter_text = self.filter_combo.currentText()
        search_text = self.search_input.text().strip().lower()
        
        filtered = []
        for q in all_questions:
            if filter_text != "All" and q.get("difficulty") != filter_text:
                continue
            if search_text and search_text not in q.get("question", "").lower():
                continue
            filtered.append(q)
        
        self.questions = {q["id"]: q for q in filtered}
        for qid, q in sorted(self.questions.items()):
            diff_display = {"easy": "[E]", "medium": "[M]", "hard": "[H]"}.get(q.get("difficulty"), "[?]")
            item = QtWidgets.QListWidgetItem(f'{diff_display} [{qid}] {q["question"][:70]}')
            item.setData(QtCore.Qt.UserRole, qid)
            self.list_widget.addItem(item)

    def show_details(self, current, previous=None):
        if not current:
            self.detail.clear()
            return
        qid = current.data(QtCore.Qt.UserRole)
        q = self.questions.get(qid)
        if not q:
            self.detail.clear()
            return
        text = []
        text.append(f'<b>ID:</b> {q["id"]}')
        text.append(f'<b>Difficulty:</b> {q.get("difficulty", "N/A")}')
        text.append(f'<b>Topic:</b> {q.get("topic", "N/A")}')
        text.append(f'<b>Question:</b> {q.get("question", "N/A")}')
        text.append('<b>Options:</b>')
        for i, opt in enumerate(q.get("options", [])):
            marker = " (correct)" if i == q.get("correct") else ""
            text.append(f'  {chr(65+i)}. {opt}{marker}')
        if q.get("explanation"):
            text.append(f'<b>Explanation:</b> {q.get("explanation")}')
        self.detail.setHtml("<br>".join(text))

    def add_question(self):
        dlg = QuestionEditorDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if not data["question"] or not data["options"]:
                QMessageBox.warning(self, "Invalid", "Question and options are required.")
                return
            self.admin.add_question(data)
            new_id = self.admin.view_all_questions()[-1]['id']
            QMessageBox.information(self, "Success", f"Question added with ID: {new_id}")
            self.refresh_questions()

    def edit_question(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Select", "Select a question to edit.")
            return
        qid = item.data(QtCore.Qt.UserRole)
        q = self.questions.get(qid)
        dlg = QuestionEditorDialog(self, question=q)
        if dlg.exec_():
            data = dlg.get_data()
            success = self.admin.edit_question(qid, data)
            if success:
                QMessageBox.information(self, "Success", "Question updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to edit question.")
            self.refresh_questions()

    def delete_question(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Select", "Select a question to delete.")
            return
        qid = item.data(QtCore.Qt.UserRole)
        if QMessageBox.question(self, "Confirm", "Delete selected question?") == QMessageBox.Yes:
            self.admin.delete_question(qid)
            self.refresh_questions()

    def backup(self):
        path = self.admin.backup_questions()
        QMessageBox.information(self, "Backup", f"Backup created: {path}")

    def reset_all(self):
        if QMessageBox.question(self, "Confirm Reset", "Remove ALL questions? This cannot be undone.") == QMessageBox.Yes:
            self.admin.reset_questions()
            self.refresh_questions()

    def show_stats(self):
        stats = self.admin.get_statistics()
        msg = f"<b>Total Questions:</b> {stats.get('total',0)}<br><br>"
        msg += "<b>By Difficulty:</b><br>"
        for k, v in stats.get("difficulty", {}).items():
            msg += f"  - {k}: {v}<br>"
        msg += "<br><b>By Topic:</b><br>"
        for k, v in stats.get("topics", {}).items():
            msg += f"  - {k}: {v}<br>"
        QMessageBox.information(self, "Statistics", msg)

    def change_password(self):
        old_pw, ok = QInputDialog.getText(self, "Change Password", "Old password:", QLineEdit.Password)
        if not ok:
            return
        new_pw, ok2 = QInputDialog.getText(self, "Change Password", "New password:", QLineEdit.Password)
        if not ok2:
            return
        if self.admin.change_password(old_pw, new_pw):
            QMessageBox.information(self, "Password", "Password changed successfully.")
        else:
            QMessageBox.warning(self, "Password", "Old password incorrect.")


def main():
    app = QApplication(sys.argv)
    
    # Use the same path as quiz_window
    qm = FileQuestionManager(QUESTIONS_PATH)
    pw_file = Path.home() / ".admin_tools" / "admin_pw.txt"
    admin = AdminToolsSimple(qm, pw_file)

    login = LoginDialog(admin)
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    w = AdminWindow(admin)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()