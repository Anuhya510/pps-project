import sys
from pathlib import Path
from typing import Dict, Any, List
import json

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QTextEdit, QMessageBox, QComboBox, QFormLayout, QDialog, QInputDialog,
    QFileDialog, QDialog, QButtonGroup, QRadioButton
)

# Import your AdminTools and QuestionManager implementations
# from modules.question_manager import QuestionManager
# from modules.admin_tools import AdminTools
# For demonstration, create a minimal stub QuestionManager if not available.

class DummyQuestionManager:
    def __init__(self):
        self._questions = {}
        self._next_id = 1

    def add_question(self, question, options, correct, difficulty, topic, explanation=""):
        qid = self._next_id
        self._next_id += 1
        self._questions[qid] = {
            "id": qid,
            "question": question,
            "options": options,
            "correct": correct,
            "difficulty": difficulty,
            "topic": topic,
            "explanation": explanation
        }
        return self._questions[qid]

    def edit_question(self, question_id, updates):
        if question_id not in self._questions:
            return False
        self._questions[question_id].update(updates)
        return True

    def delete_question(self, question_id):
        return self._questions.pop(question_id, None) is not None

    def get_all_questions_flat(self):
        return list(self._questions.values())

    def reset_all(self):
        self._questions.clear()
        self._next_id = 1

    def backup(self):
        path = Path.cwd() / "questions_backup.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.get_all_questions_flat(), f, indent=2)
        return path

    def get_statistics(self):
        total = len(self._questions)
        difficulty = {}
        topics = {}
        for q in self._questions.values():
            difficulty[q["difficulty"]] = difficulty.get(q["difficulty"], 0) + 1
            topics[q["topic"]] = topics.get(q["topic"], 0) + 1
        return {"total": total, "difficulty": difficulty, "topics": topics}

# Replace DummyQuestionManager with your real one when available
QuestionManager = DummyQuestionManager

from hashlib import sha256

class AdminToolsSimple:
    # Minimal reimplementation to avoid circular imports in demo
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

    # delegate to question manager
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

# GUI classes

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
        self.correct_edit = QLineEdit()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard"])
        self.topic_edit = QLineEdit()
        self.explanation_edit = QTextEdit()

        form.addRow("Question:", self.question_edit)
        form.addRow("Options (one per line):", self.options_edit)
        form.addRow("Correct option (exact text):", self.correct_edit)
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

    def _load_question(self):
        self.question_edit.setPlainText(self.question.get("question", ""))
        self.options_edit.setPlainText("\n".join(self.question.get("options", [])))
        self.correct_edit.setText(str(self.question.get("correct", "")))
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
            "correct": self.correct_edit.text().strip(),
            "difficulty": self.difficulty_combo.currentText(),
            "topic": self.topic_edit.text().strip(),
            "explanation": self.explanation_edit.toPlainText().strip()
        }



class AdminWindow(QWidget):
    def __init__(self, admin_tools: AdminToolsSimple):
        super().__init__()
        self.setWindowTitle("Admin Tools")
        self.resize(900, 600)
        self.admin = admin_tools
        sys_btns = QHBoxLayout()
        self.quiz_btn = QPushButton("Take Quiz")
        sys_btns.addWidget(self.quiz_btn)
        self.quiz_btn.clicked.connect(self.take_quiz)

        main_layout = QHBoxLayout(self)

        # Left: question list and actions
        left = QVBoxLayout()
        self.list_widget = QListWidget()
        left.addWidget(QLabel("Questions"))
        left.addWidget(self.list_widget)

        list_btns = QHBoxLayout()
        self.add_btn = QPushButton("Add")
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
        right.addWidget(QLabel("Details"))
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
        self.questions = {q["id"]: q for q in self.admin.view_all_questions()}
        for qid, q in sorted(self.questions.items()):
            item = QtWidgets.QListWidgetItem(f'{qid}: {q["question"][:80]}')
            item.setData(QtCore.Qt.UserRole, qid)
            self.list_widget.addItem(item)
        self.detail.clear()

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
        text.append(f'ID: {q["id"]}')
        text.append(f'Question: {q["question"]}')
        text.append("Options:")
        for opt in q.get("options", []):
            text.append(f'  - {opt}')
        text.append(f'Correct: {q.get("correct")}')
        text.append(f'Difficulty: {q.get("difficulty")}')
        text.append(f'Topic: {q.get("topic")}')
        text.append(f'Explanation: {q.get("explanation","")}')
        self.detail.setPlainText("\n".join(text))

    def add_question(self):
        dlg = QuestionEditorDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            if not data["question"] or not data["options"]:
                QMessageBox.warning(self, "Invalid", "Question and options are required.")
                return
            self.admin.add_question(data)
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
            # Do not allow changing difficulty structure? we allow update here
            success = self.admin.edit_question(qid, data)
            if not success:
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
        msg = f"Total: {stats.get('total',0)}\n\nDifficulty:\n"
        for k,v in stats.get("difficulty",{}).items():
            msg += f"  {k}: {v}\n"
        msg += "\nTopics:\n"
        for k,v in stats.get("topics",{}).items():
            msg += f"  {k}: {v}\n"
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

    def take_quiz(self):
        questions = self.admin.view_all_questions()
        if not questions:
           QMessageBox.information(self, "No Questions", "There are no questions to take.")
        return
        dlg = QuizDialog(self, questions)
        dlg.exec_()
        

import json
from pathlib import Path
from typing import List, Dict, Any

class FileQuestionManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])
        self._load()

    def _load(self):
        with self.path.open("r", encoding="utf-8") as f:
            self._questions: List[Dict[str, Any]] = json.load(f)
        # ensure ids and next id
        self._by_id = {q["id"]: q for q in self._questions}
        self._next_id = max((q["id"] for q in self._questions), default=0) + 1

    def _write(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # API expected by AdminToolsSimple
    def add_question(self, question, options, correct, difficulty, topic, explanation=""):
        q = {
            "id": self._next_id,
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
        # update allowed fields
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
            difficulty[q.get("difficulty", "unknown")] = difficulty.get(q.get("difficulty","unknown"), 0) + 1
            topics[q.get("topic", "unknown")] = topics.get(q.get("topic","unknown"), 0) + 1
        return {"total": total, "difficulty": difficulty, "topics": topics}

class QuizDialog(QDialog):
    def __init__(self, parent, questions: List[Dict[str, Any]]):
        super().__init__(parent)
        self.setWindowTitle("Quiz")
        self.resize(700, 500)
        self.engine = QuizEngine(questions)

        # default distribution: use available counts or smaller if not enough

        try:
            self.engine.generate_quiz()
        except Exception:
            # fallback: generate with whatever is available per difficulty
            # count  = min( len(list), default ) handled by adjusting distribution
            dist = {}
            for lvl in ("easy","medium","hard"):
                dist[lvl] = min(2, len([q for q in questions if q.get("difficulty")==lvl]))
            # ensure at least 1 question
            if sum(dist.values()) == 0:
                raise ValueError("No questions available for quiz")
            self.engine.generate_quiz(dist)

        layout = QVBoxLayout(self)

        self.q_label = QLabel("")
        self.q_label.setWordWrap(True)
        layout.addWidget(self.q_label)

        self.options_group = QButtonGroup(self)
        self.option_buttons: List[QRadioButton] = []
        for i in range(4):  # up to 4 options; will hide unused
            rb = QRadioButton("")
            self.options_group.addButton(rb, i)
            self.option_buttons.append(rb)
            layout.addWidget(rb)

        nav = QHBoxLayout()
        self.submit_btn = QPushButton("Submit")
        self.next_btn = QPushButton("Next")
        self.next_btn.setEnabled(False)
        nav.addWidget(self.submit_btn)
        nav.addWidget(self.next_btn)
        layout.addLayout(nav)

        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        self.submit_btn.clicked.connect(self.on_submit)
        self.next_btn.clicked.connect(self.on_next)

        self.show_question()

    def show_question(self):
        if not self.engine.has_next_question():
            self.finish()
            return
        q = self.engine.get_next_question()
        self.q_label.setText(q.get("question",""))
        opts = q.get("options", [])
        for i, rb in enumerate(self.option_buttons):
            if i < len(opts):
                rb.setText(opts[i])
                rb.show()
                rb.setChecked(False)
            else:
                rb.hide()
        self.submit_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        prog = self.engine.get_progress()
        self.progress_label.setText(f'Question {prog["current"]}/{prog["total"]} — Score: {prog["score_so_far"]}')

    def on_submit(self):
        selected_id = self.options_group.checkedId()
        if selected_id == -1:
            QMessageBox.information(self, "Select", "Please select an option.")
            return
        try:
            is_correct = self.engine.submit_answer(selected_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        QMessageBox.information(self, "Result", "Correct!" if is_correct else "Incorrect.")
        self.submit_btn.setEnabled(False)
        self.next_btn.setEnabled(True)

    def on_next(self):
        if self.engine.has_next_question():
            self.show_question()
        else:
            self.finish()

    def finish(self):
        results = self.engine.get_results()
        summary = results["summary"]
        msg = f"Score: {summary['score']}/{summary['total']} ({summary['percentage']}%)"
        detailed = "\n\n".join(
            f"Q: {a['question']}\nYour: {a['selected_option']}\nCorrect: {a['correct_option']}\n"
            for a in results["answers"]
        )
        QMessageBox.information(self, "Quiz Finished", msg + "\n\nDetails in console.")
        # optionally print detailed answers to console for review
        print(detailed)
        self.accept()


def main():
    app = QApplication(sys.argv)

    # initialize components - replace paths and real QM as needed
    qm = FileQuestionManager(Path.home() / ".admin_tools" / "questions.json")
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
