import random
from typing import List, Dict, Any, Optional


class QuizEngine:
    """
    QuizEngine handles the core quiz functionality.

    Responsibilities:
    - Generate quiz based on difficulty distribution
    - Control quiz flow (next question, answer submission)
    - Track score and progress
    - Return structured results for analytics or GUI
    """

    def __init__(self, questions: List[Dict[str, Any]]):
        """
        Initialize QuizEngine with a flat list of questions.

        Args:
            questions: List of question dictionaries

        Raises:
            TypeError: If questions is not a list
            ValueError: If questions list is empty
        """
        if not isinstance(questions, list):
            raise TypeError("Questions must be a list")

        if not questions:
            raise ValueError("Questions list cannot be empty")

        self.questions = questions

        # Group questions by difficulty for efficient selection
        self.grouped_questions = {
            "easy": [q for q in questions if q.get("difficulty") == "easy"],
            "medium": [q for q in questions if q.get("difficulty") == "medium"],
            "hard": [q for q in questions if q.get("difficulty") == "hard"]
        }

        # Quiz state variables
        self.selected_questions: List[Dict[str, Any]] = []
        self.score: int = 0
        self.current_index: int = 0
        self.user_answers: List[Dict[str, Any]] = []

    # ---------------------------
    # QUIZ GENERATION
    # ---------------------------

    def generate_quiz(self, distribution: Optional[Dict[str, int]] = None) -> None:
        """
        Generate a quiz using difficulty distribution.

        Default distribution:
            easy: 3, medium: 3, hard: 4

        Args:
            distribution: Dict specifying number of questions per difficulty

        Raises:
            ValueError: If invalid distribution or insufficient questions
        """
        if distribution is None:
            distribution = {"easy": 3, "medium": 3, "hard": 4}

        selected = []

        for level, count in distribution.items():

            # Check if difficulty level exists
            if level not in self.grouped_questions:
                raise ValueError(f"Invalid difficulty level: {level}")

            # Ensure valid count
            if count <= 0:
                raise ValueError(f"Count for {level} must be positive")

            available_questions = self.grouped_questions[level]

            # Ensure enough questions exist
            if len(available_questions) < count:
                raise ValueError(
                    f"Not enough {level} questions. "
                    f"Available: {len(available_questions)}, Required: {count}"
                )

            # Randomly select questions without repetition
            selected.extend(random.sample(available_questions, count))

        # Shuffle final quiz order
        random.shuffle(selected)

        # Set selected questions and reset state
        self.selected_questions = selected
        self.reset_quiz()

    # ---------------------------
    # QUIZ FLOW
    # ---------------------------

    def has_next_question(self) -> bool:
        """
        Check if more questions are available.

        Returns:
            True if more questions exist, else False
        """
        return self.current_index < len(self.selected_questions)

    def get_next_question(self) -> Dict[str, Any]:
        """
        Get the next question in the quiz.

        Returns:
            Question dictionary

        Raises:
            ValueError: If quiz not generated
            IndexError: If no more questions
        """
        if not self.selected_questions:
            raise ValueError("Quiz not generated. Call generate_quiz() first.")

        if not self.has_next_question():
            raise IndexError("No more questions available")

        return self.selected_questions[self.current_index]

    def submit_answer(self, answer_index: int) -> bool:
        """
        Submit an answer for the current question.

        Args:
            answer_index: Selected option index (0-based)

        Returns:
            True if answer is correct, else False

        Raises:
            ValueError, TypeError, IndexError, KeyError
        """
        if not self.selected_questions:
            raise ValueError("Quiz not generated. Call generate_quiz() first.")

        if not self.has_next_question():
            raise IndexError("No active question to answer")

        question = self.selected_questions[self.current_index]

        # Validate required fields
        if "correct" not in question or "options" not in question:
            raise KeyError("Invalid question format")

        correct_index = question["correct"]

        # Ensure correct index is valid
        if not (0 <= correct_index < len(question["options"])):
            raise ValueError("Invalid correct answer index in question data")

        # Validate user input
        if not isinstance(answer_index, int):
            raise TypeError("Answer must be an integer index")

        if not (0 <= answer_index < len(question["options"])):
            raise ValueError("Invalid answer index")

        is_correct = (answer_index == correct_index)

        # Store detailed answer info (used for analytics/GUI)
        self.user_answers.append({
            "question_id": question.get("id"),
            "question": question.get("question"),
            "selected_option": question["options"][answer_index],
            "correct_option": question["options"][correct_index],
            "is_correct": is_correct,
            "difficulty": question.get("difficulty"),
            "topic": question.get("topic"),
            "explanation": question.get("explanation", "")
        })

        # Update score if correct
        if is_correct:
            self.score += 1

        # Move to next question
        self.current_index += 1
        return is_correct

    # ---------------------------
    # PROGRESS TRACKING
    # ---------------------------

    def get_progress(self) -> Dict[str, Any]:
        """
        Get quiz progress details.

        Returns:
            Dictionary with progress info
        """
        if not self.selected_questions:
            raise ValueError("Quiz not generated.")

        return {
            "current": self.current_index + 1,
            "total": len(self.selected_questions),
            "remaining": len(self.selected_questions) - self.current_index,
            "score_so_far": self.score
        }

    def get_score(self) -> int:
        """
        Return current score.
        """
        return self.score

    # ---------------------------
    # RESULTS
    # ---------------------------

    def get_results(self) -> Dict[str, Any]:
        """
        Get final quiz results.

        Returns:
            Dictionary with summary and detailed answers
        """
        if not self.selected_questions:
            raise ValueError("Quiz not generated.")

        total = len(self.selected_questions)
        percentage = (self.score / total) * 100 if total > 0 else 0

        return {
            "summary": {
                "score": self.score,
                "total_questions": total,
                "percentage": round(percentage, 2)
            },
            "answers": self.user_answers
        }

    # ---------------------------
    # RESET / CONTROL
    # ---------------------------

    def reset_quiz(self) -> None:
        """
        Reset quiz progress.
        """
        self.score = 0
        self.current_index = 0
        self.user_answers = []

    def restart_quiz(self) -> None:
        """
        Restart quiz (alias for reset).
        """
        self.reset_quiz()

    # ---------------------------
    # STATIC HELPERS
    # ---------------------------

    @staticmethod
    def filter_by_difficulty(
        questions: List[Dict[str, Any]],
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Filter questions by difficulty.
        """
        difficulty = difficulty.lower()
        return [q for q in questions if q.get("difficulty", "").lower() == difficulty]

    @staticmethod
    def filter_by_topic(
        questions: List[Dict[str, Any]],
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Filter questions by topic.
        """
        topic = topic.lower()
        return [q for q in questions if q.get("topic", "").lower() == topic]