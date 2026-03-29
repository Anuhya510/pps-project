from pathlib import Path
from typing import Dict, Any, List
import hashlib

from modules.question_manager import QuestionManager


class AdminTools:
    """
    AdminTools provides higher-level operations for managing the quiz system.

    Responsibilities:
    - Secure admin authentication
    - Managing questions through QuestionManager
    - Providing simplified interfaces for admin actions
    """

    def __init__(self, qm: QuestionManager, password_file: Path):
        """
        Initialize AdminTools with:
        - QuestionManager instance (for data operations)
        - Password file (for admin authentication)
        """
        self.qm = qm
        self.password_file = password_file
        self._ensure_password_file()

    # ---------------------------
    # PASSWORD MANAGEMENT
    # ---------------------------

    def _ensure_password_file(self) -> None:
        """
        Ensure that the admin password file exists.

        If not present, a default password is created.
        This prevents login errors when the system runs for the first time.
        """
        self.password_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.password_file.exists():
            default_password = "admin123"
            self._write_password(default_password)

    def _hash_password(self, password: str) -> str:
        """
        Convert plain text password into a secure hashed format.

        Hashing ensures that the actual password is not stored directly,
        improving basic security.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def _write_password(self, password: str) -> None:
        """
        Store the hashed password in the file.
        """
        hashed = self._hash_password(password)

        with self.password_file.open("w", encoding="utf-8") as f:
            f.write(hashed)

    def verify_password(self, password: str) -> bool:
        """
        Verify if the entered password matches the stored password.
        """
        if not self.password_file.exists():
            return False

        with self.password_file.open("r", encoding="utf-8") as f:
            stored_password = f.read().strip()

        return stored_password == self._hash_password(password)

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change the admin password.

        The old password must be verified before updating.
        """
        if not self.verify_password(old_password):
            return False

        self._write_password(new_password)
        return True

    # ---------------------------
    # QUESTION MANAGEMENT
    # ---------------------------

    def add_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new question using QuestionManager.

        This method acts as a wrapper to simplify input handling.
        """
        return self.qm.add_question(
            question=data["question"],
            options=data["options"],
            correct=data["correct"],
            difficulty=data["difficulty"],
            topic=data["topic"],
            explanation=data.get("explanation", "")
        )

    def edit_question(self, question_id: int, updates: Dict[str, Any]) -> bool:
        """
        Edit an existing question.

        Note:
        - Difficulty cannot be changed to maintain data structure consistency.
        """
        return self.qm.edit_question(question_id, updates)

    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question using its ID.
        """
        return self.qm.delete_question(question_id)

    def view_all_questions(self) -> List[Dict[str, Any]]:
        """
        Retrieve all questions in a flat list format.

        This is useful for displaying questions in admin panels.
        """
        return self.qm.get_all_questions_flat()

    # ---------------------------
    # SYSTEM OPERATIONS
    # ---------------------------

    def reset_questions(self) -> None:
        """
        Remove all questions from the system.

        This action should be used carefully as it clears all data.
        """
        self.qm.reset_all()

    def backup_questions(self) -> Path:
        """
        Create a backup of the question bank.

        Useful before performing major modifications.
        """
        return self.qm.backup()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the question bank.

        This includes total count, difficulty distribution, and topics.
        """
        return self.qm.get_statistics()