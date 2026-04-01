from typing import Dict, List, Any, Optional

from utils.exceptions import (
    InvalidQuestionError,
    InvalidStudentError,
    InvalidQuizSettingsError
)


def validate_student_name(name: str) -> bool:
    """
    Validate student name.

    Rules:
    - Must be a string
    - Must not be empty
    - Must contain at least 2 characters
    - Must contain only letters, spaces, hyphens, and apostrophes
    """

    # Check if the name is a string
    if not isinstance(name, str):
        raise InvalidStudentError("Student name must be a string.")

    # Remove extra spaces from beginning and end
    cleaned_name = name.strip()

    # Check if name is empty after removing spaces
    if not cleaned_name:
        raise InvalidStudentError("Student name cannot be empty.")

    # Ensure name has at least 2 characters
    if len(cleaned_name) < 2:
        raise InvalidStudentError("Student name must contain at least 2 characters.")

    # Allow only letters, spaces, hyphens, and apostrophes
    if not all(
        char.isalpha() or char.isspace() or char in ["-", "'"]
        for char in cleaned_name
    ):
        raise InvalidStudentError(
            "Student name can only contain letters, spaces, hyphens, and apostrophes."
        )

    return True


def validate_question_data(question: Dict[str, Any]) -> bool:
    """
    Validate question dictionary structure.

    Required fields:
    - id
    - question
    - options
    - answer
    - topic
    - difficulty
    """

    # Ensure the question data is a dictionary
    if not isinstance(question, dict):
        raise InvalidQuestionError("Question data must be a dictionary.")

    # List of required fields that every question must contain
    required_fields = [
        "id",
        "question",
        "options",
        "answer",
        "topic",
        "difficulty"
    ]

    # Check if all required fields exist
    for field in required_fields:
        if field not in question:
            raise InvalidQuestionError(f"Missing required field: {field}")

    # Validate question text
    if not isinstance(question["question"], str) or not question["question"].strip():
        raise InvalidQuestionError("Question text must be a non-empty string.")

    # Validate options list
    if not isinstance(question["options"], list):
        raise InvalidQuestionError("Options must be a list.")

    # Ensure there are at least 2 options
    if len(question["options"]) < 2:
        raise InvalidQuestionError("A question must have at least 2 options.")

    # Ensure every option is a non-empty string
    if not all(
        isinstance(option, str) and option.strip()
        for option in question["options"]
    ):
        raise InvalidQuestionError("All options must be non-empty strings.")

    # Validate answer field
    if not isinstance(question["answer"], str) or not question["answer"].strip():
        raise InvalidQuestionError("Answer must be a non-empty string.")

    # Ensure the answer exists inside the options list
    if question["answer"] not in question["options"]:
        raise InvalidQuestionError("Correct answer must exist in options list.")

    # Validate topic field
    if not isinstance(question["topic"], str) or not question["topic"].strip():
        raise InvalidQuestionError("Topic must be a non-empty string.")

    # Validate difficulty field
    if not isinstance(question["difficulty"], str):
        raise InvalidQuestionError("Difficulty must be a string.")

    # Allowed difficulty levels
    valid_difficulties = ["easy", "medium", "hard"]

    # Ensure difficulty is one of the allowed values
    if question["difficulty"].lower() not in valid_difficulties:
        raise InvalidQuestionError(
            f"Difficulty must be one of: {', '.join(valid_difficulties)}"
        )

    return True


def validate_quiz_settings(
    num_questions: int,
    difficulty: Optional[str] = None,
    topic: Optional[str] = None
) -> bool:
    """
    Validate quiz setup settings.

    Args:
        num_questions: Number of questions requested
        difficulty: Selected difficulty level
        topic: Selected topic
    """

    # Ensure number of questions is an integer
    if not isinstance(num_questions, int):
        raise InvalidQuizSettingsError("Number of questions must be an integer.")

    # Ensure the number is greater than 0
    if num_questions <= 0:
        raise InvalidQuizSettingsError("Number of questions must be greater than 0.")

    # Validate difficulty only if it was provided
    if difficulty is not None:
        if not isinstance(difficulty, str):
            raise InvalidQuizSettingsError("Difficulty must be a string.")

        # Allowed difficulty levels
        valid_difficulties = ["easy", "medium", "hard"]

        # Ensure selected difficulty is valid
        if difficulty.lower() not in valid_difficulties:
            raise InvalidQuizSettingsError(
                f"Difficulty must be one of: {', '.join(valid_difficulties)}"
            )

    # Validate topic only if it was provided
    if topic is not None:
        if not isinstance(topic, str) or not topic.strip():
            raise InvalidQuizSettingsError(
                "Topic must be a valid non-empty string."
            )

    return True


def validate_answer_choice(choice: str, options: List[str]) -> bool:
    """
    Validate whether a student's selected answer exists
    in the available options list.
    """

    # Ensure selected answer is a non-empty string
    if not isinstance(choice, str) or not choice.strip():
        raise InvalidQuestionError("Selected answer must be a non-empty string.")

    # Ensure options are provided as a list
    if not isinstance(options, list):
        raise InvalidQuestionError("Options must be provided as a list.")

    # Ensure every option in the list is a string
    if not all(isinstance(option, str) for option in options):
        raise InvalidQuestionError("All options must be strings.")

    # Ensure the selected choice exists in the available options
    if choice not in options:
        raise InvalidQuestionError(
            f"Selected answer must be one of: {', '.join(options)}"
        )

    return True