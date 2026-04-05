import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionManager:
    """
    QuestionManager handles all operations related to the question bank.
    """

    def __init__(self, data_file: Path):
        """
        Initialize the QuestionManager with the path to the JSON file.
        """
        self.data_file = data_file
        self._ensure_file_exists()

    # ---------------------------
    # FILE HANDLING METHODS
    # ---------------------------

    def _ensure_file_exists(self) -> None:
        """Ensure that the JSON file exists with proper structure."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.data_file.exists():
            default_data = {
                "easy": [],
                "medium": [],
                "hard": []
            }
            self._write_data(default_data)
            logger.info("Created new questions.json file.")

    def _read_data(self):
        """
        Read and return data from the JSON file.
        Handles both list and dictionary formats.
        """
        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                
                # If data is a list, convert to dictionary format
                if isinstance(data, list):
                    categorized = {"easy": [], "medium": [], "hard": []}
                    for q in data:
                        diff = q.get("difficulty", "medium")
                        if diff in categorized:
                            categorized[diff].append(q)
                        else:
                            categorized["medium"].append(q)
                    return categorized
                
                return data
        except json.JSONDecodeError:
            logger.error("JSON file is corrupted or improperly formatted.")
            raise
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise

    def _write_data(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Write updated data back to the JSON file."""
        try:
            with self.data_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            raise

    # ---------------------------
    # INTERNAL HELPER METHODS
    # ---------------------------

    def _get_next_id(self, data: Dict[str, List[Dict[str, Any]]]) -> int:
        """Generate a unique ID for a new question."""
        all_questions = []
        for level in data.values():
            all_questions.extend(level)
        return max((q.get("id", 0) for q in all_questions), default=0) + 1

    # ---------------------------
    # CRUD OPERATIONS
    # ---------------------------

    def add_question(
        self,
        question: str,
        options: List[str],
        correct: int,
        difficulty: str,
        topic: str,
        explanation: str = ""
    ) -> Dict[str, Any]:
        """Add a new question to the question bank."""
        data = self._read_data()

        if difficulty not in data:
            raise ValueError("Difficulty must be 'easy', 'medium', or 'hard'")

        if len(options) < 2:
            raise ValueError("A question must have at least two options")

        if correct < 0 or correct >= len(options):
            raise ValueError("Correct option index is out of range")

        new_question = {
            "id": self._get_next_id(data),
            "question": question,
            "options": options,
            "correct": correct,
            "difficulty": difficulty,
            "topic": topic,
            "explanation": explanation
        }

        data[difficulty].append(new_question)
        self._write_data(data)

        logger.info(f"Added question ID {new_question['id']}")
        return new_question

    def edit_question(self, question_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing question."""
        data = self._read_data()

        if "difficulty" in updates:
            raise ValueError("Changing difficulty is not allowed")

        for level in data:
            for q in data[level]:
                if q.get("id") == question_id:
                    q.update(updates)
                    self._write_data(data)
                    logger.info(f"Updated question ID {question_id}")
                    return True

        logger.warning(f"Question ID {question_id} not found")
        return False

    def delete_question(self, question_id: int) -> bool:
        """Delete a question using its ID."""
        data = self._read_data()
        found = False

        for level in data:
            new_list = [q for q in data[level] if q.get("id") != question_id]
            if len(new_list) != len(data[level]):
                data[level] = new_list
                found = True

        if not found:
            logger.warning(f"Question ID {question_id} not found")
            return False

        self._write_data(data)
        logger.info(f"Deleted question ID {question_id}")
        return True

    # ---------------------------
    # DATA RETRIEVAL METHODS
    # ---------------------------

    def get_all_questions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return all questions grouped by difficulty."""
        return self._read_data()

    def get_all_questions_flat(self) -> List[Dict[str, Any]]:
        """Return all questions as a single list."""
        data = self._read_data()
        all_qs = []

        for level in data.values():
            if isinstance(level, list):
                all_qs.extend(level)

        return all_qs

    def get_questions_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """Return questions of a specific difficulty level."""
        data = self._read_data()
        difficulty = difficulty.lower()
        if difficulty not in data:
            raise ValueError("Invalid difficulty level")
        return data[difficulty]

    # ---------------------------
    # STATISTICS
    # ---------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Generate useful statistics about the question bank."""
        data = self._read_data()

        stats = {
            "total": 0,
            "by_difficulty": {},
            "by_topic": {}
        }

        for level, questions in data.items():
            stats["by_difficulty"][level] = len(questions)
            stats["total"] += len(questions)

            for q in questions:
                topic = q.get("topic", "Unknown")
                stats["by_topic"][topic] = stats["by_topic"].get(topic, 0) + 1

        return stats

    # ---------------------------
    # BACKUP
    # ---------------------------

    def backup(self) -> Path:
        """Create a backup of the current question file."""
        backup_file = self.data_file.parent / f"questions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            import shutil
            shutil.copy2(self.data_file, backup_file)
            logger.info(f"Backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    # ---------------------------
    # RESET
    # ---------------------------

    def reset_all(self) -> None:
        """Remove all questions from the file."""
        empty_data = {
            "easy": [],
            "medium": [],
            "hard": []
        }
        self._write_data(empty_data)
        logger.warning("All questions have been reset!")

    def get_question_by_id(self, question_id: int) -> Dict[str, Any]:
        """Get a single question by its ID."""
        data = self._read_data()
        for level in data.values():
            for q in level:
                if q.get("id") == question_id:
                    return q
        return None