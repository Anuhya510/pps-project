class QuizError(Exception):
    """
    Base exception class for the quiz application.

    All custom quiz-related exceptions should inherit from this class.
    """
    pass


class InvalidQuestionError(QuizError):
    """
    Raised when question data is missing required fields
    or contains invalid values.
    """
    pass


class InvalidStudentError(QuizError):
    """
    Raised when student name or student data is invalid.
    """
    pass


class InvalidQuizSettingsError(QuizError):
    """
    Raised when quiz settings are incorrect.

    Example:
    - Negative question count
    - Invalid difficulty selection
    - Invalid topic selection
    """
    pass


class QuestionNotFoundError(QuizError):
    """
    Raised when a question with a given ID cannot be found.
    """
    pass


class DuplicateQuestionError(QuizError):
    """
    Raised when trying to add a question
    with an ID that already exists.
    """
    pass


class EmptyQuestionBankError(QuizError):
    """
    Raised when no questions are available in the question bank.
    """
    pass


class AuthenticationError(QuizError):
    """
    Raised when admin authentication fails.
    """
    pass


class QuizExecutionError(QuizError):
    """
    Raised when an error occurs during quiz execution.

    Example:
    - Quiz submitted before answering
    - Timer expired unexpectedly
    - Quiz session data missing
    """
    pass


class FileLoadError(QuizError):
    """
    Raised when a required file cannot be loaded.

    Example:
    - questions.json missing
    - student history file corrupted
    """
    pass


class FileSaveError(QuizError):
    """
    Raised when a file cannot be saved properly.
    """
    pass