from typing import Dict, List, Any, Optional
from collections import defaultdict
# Type aliases used to make type hints easier to read
AnalysisStats = Dict[str, Dict[str, Any]]
WeakArea = Dict[str, Any]


class ScoreAnalyzer:
    """
    ScoreAnalyzer takes quiz results from QuizEngine and generates
    useful performance insights such as:

    - Topic-wise performance
    - Difficulty-wise performance
    - Weak areas
    - Strongest area
    - Mastery levels
    - Recommendations
    - Final grade
    """

    # --------------------------------------------------
    # CLASS CONSTANTS
    # --------------------------------------------------
    # These values are stored here so they can be changed
    # easily later without modifying the logic everywhere.

    WEAK_AREA_THRESHOLD = 60.0
    RECOMMENDATION_THRESHOLD = 70.0

    MASTERED_THRESHOLD = 80.0
    PROFICIENT_THRESHOLD = 60.0
    DEVELOPING_THRESHOLD = 40.0

    GRADE_A_PLUS = 95.0
    GRADE_A = 90.0
    GRADE_B_PLUS = 85.0
    GRADE_B = 80.0
    GRADE_C_PLUS = 75.0
    GRADE_C = 70.0
    GRADE_D = 60.0

    def _init_(self, quiz_results: Dict[str, Any]):
        """
        Initialize the analyzer with quiz results.

        Expected structure:
        {
            "summary": {
                "score": int,
                "total_questions": int,
                "percentage": float
            },
            "answers": [...]
        }
        """

        # Store the original quiz results
        self.results = quiz_results

        # Safely store summary data
        # If summary is missing, use default values
        self.summary = quiz_results.get(
            "summary",
            {
                "score": 0,
                "total_questions": 0,
                "percentage": 0.0
            }
        )

        # Safely store answer list
        # If answers are missing, use an empty list
        self.answers = quiz_results.get("answers", [])

    # --------------------------------------------------
    # INTERNAL HELPER METHODS
    # --------------------------------------------------

    def _calculate_percentage(self, correct: int, total: int) -> float:
        """
        Calculate percentage safely.

        Example:
        correct = 8, total = 10
        returns 80.0
        """
        return round((correct / total) * 100, 2) if total > 0 else 0.0

    def _build_analysis(
        self,
        group_key: str,
        default_label: str
    ) -> AnalysisStats:
        """
        Generic helper function used to group answers by topic
        or difficulty.

        Example:
        group_key = "topic"
        group_key = "difficulty"
        """

        # defaultdict automatically creates the dictionary
        # structure for a new topic/difficulty
        stats = defaultdict(
            lambda: {
                "correct": 0,
                "total": 0,
                "percentage": 0.0
            }
        )

        # Loop through each answer in the quiz
        for answer in self.answers:

            # Get the category name (topic or difficulty)
            # If missing, use the default label
            category = answer.get(group_key, default_label)

            # Increase total question count for that category
            stats[category]["total"] += 1

            # Increase correct count if answer was correct
            if answer.get("is_correct", False):
                stats[category]["correct"] += 1

        # After collecting counts, calculate percentages
        for category, values in stats.items():
            values["percentage"] = self._calculate_percentage(
                values["correct"],
                values["total"]
            )

        return dict(stats)

    def _classify_mastery(self, percentage: float) -> str:
        """
        Convert a percentage into a mastery level.
        """

        if percentage >= self.MASTERED_THRESHOLD:
            return "Mastered"
        elif percentage >= self.PROFICIENT_THRESHOLD:
            return "Proficient"
        elif percentage >= self.DEVELOPING_THRESHOLD:
            return "Developing"

        return "Needs Improvement"

    def _calculate_grade(self, percentage: float) -> str:
        """
        Convert percentage into a letter grade.
        """

        if percentage >= self.GRADE_A_PLUS:
            return "A+"
        elif percentage >= self.GRADE_A:
            return "A"
        elif percentage >= self.GRADE_B_PLUS:
            return "B+"
        elif percentage >= self.GRADE_B:
            return "B"
        elif percentage >= self.GRADE_C_PLUS:
            return "C+"
        elif percentage >= self.GRADE_C:
            return "C"
        elif percentage >= self.GRADE_D:
            return "D"

        return "F"

    # --------------------------------------------------
    # ANALYSIS METHODS
    # --------------------------------------------------

    def analyze_by_difficulty(self) -> AnalysisStats:
        """
        Analyze student performance grouped by difficulty level.
        """

        return self._build_analysis(
            group_key="difficulty",
            default_label="Unknown"
        )

    def analyze_by_topic(self) -> AnalysisStats:
        """
        Analyze student performance grouped by topic.
        """

        return self._build_analysis(
            group_key="topic",
            default_label="Unknown"
        )

    # --------------------------------------------------
    # WEAK AREA METHODS
    # --------------------------------------------------

    def identify_weak_areas(
        self,
        topic_analysis: Optional[AnalysisStats] = None,
        difficulty_analysis: Optional[AnalysisStats] = None,
        threshold: float = WEAK_AREA_THRESHOLD
    ) -> List[WeakArea]:
        """
        Identify weak topics and difficulty levels.

        Any topic/difficulty with percentage below threshold
        is considered a weak area.
        """

        weak_areas = []

        # Use existing analysis if already calculated
        # Otherwise calculate it now
        topic_analysis = topic_analysis or self.analyze_by_topic()
        difficulty_analysis = (
            difficulty_analysis or self.analyze_by_difficulty()
        )

        # Check weak topics
        for topic, stats in topic_analysis.items():
            if stats["percentage"] < threshold:
                weak_areas.append({
                    "type": "topic",
                    "name": topic,
                    "correct": stats["correct"],
                    "total": stats["total"],
                    "percentage": stats["percentage"],
                    "recommendation": f"Review {topic} concepts"
                })

        # Check weak difficulty levels
        for difficulty, stats in difficulty_analysis.items():
            if stats["percentage"] < threshold:
                weak_areas.append({
                    "type": "difficulty",
                    "name": difficulty,
                    "correct": stats["correct"],
                    "total": stats["total"],
                    "percentage": stats["percentage"],
                    "recommendation": (
                        f"Practice more {difficulty} level questions"
                    )
                })

        # Sort weak areas from lowest score to highest score
        weak_areas.sort(key=lambda area: area["percentage"])

        return weak_areas

    # --------------------------------------------------
    # STRONGEST AREA METHOD
    # --------------------------------------------------

    def identify_strongest_area(
        self,
        topic_analysis: Optional[AnalysisStats] = None,
        difficulty_analysis: Optional[AnalysisStats] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the strongest topic or difficulty level.
        """

        topic_analysis = topic_analysis or self.analyze_by_topic()
        difficulty_analysis = (
            difficulty_analysis or self.analyze_by_difficulty()
        )

        strongest_area = None

        # Compare all topics
        for topic, stats in topic_analysis.items():
            current_area = {
                "type": "topic",
                "name": topic,
                "percentage": stats["percentage"]
            }

            if (
                strongest_area is None or
                current_area["percentage"] > strongest_area["percentage"]
            ):
                strongest_area = current_area

        # Compare all difficulty levels
        for difficulty, stats in difficulty_analysis.items():
            current_area = {
                "type": "difficulty",
                "name": difficulty,
                "percentage": stats["percentage"]
            }

            if (
                strongest_area is None or
                current_area["percentage"] > strongest_area["percentage"]
            ):
                strongest_area = current_area

        return strongest_area

    # --------------------------------------------------
    # MASTERY LEVEL METHODS
    # --------------------------------------------------

    def get_mastery_levels(
        self,
        topic_analysis: Optional[AnalysisStats] = None,
        difficulty_analysis: Optional[AnalysisStats] = None
    ) -> Dict[str, str]:
        """
        Generate mastery level labels for each topic and difficulty.
        """

        mastery_levels = {}

        topic_analysis = topic_analysis or self.analyze_by_topic()
        difficulty_analysis = (
            difficulty_analysis or self.analyze_by_difficulty()
        )

        # Add mastery labels for topics
        for topic, stats in topic_analysis.items():
            mastery_levels[f"topic_{topic}"] = (
                self._classify_mastery(stats["percentage"])
            )

        # Add mastery labels for difficulty levels
        for difficulty, stats in difficulty_analysis.items():
            mastery_levels[f"difficulty_{difficulty}"] = (
                self._classify_mastery(stats["percentage"])
            )

        return mastery_levels

    # --------------------------------------------------
    # RECOMMENDATION METHODS
    # --------------------------------------------------

    def get_recommendations(
        self,
        weak_areas: Optional[List[WeakArea]] = None
    ) -> List[str]:
        """
        Generate recommendations for the student based on weak areas.
        """

        recommendations = []

        # Reuse existing weak area analysis if available
        weak_areas = weak_areas or self.identify_weak_areas(
            threshold=self.RECOMMENDATION_THRESHOLD
        )

        # Add recommendation for each weak area
        for area in weak_areas:
            if area["type"] == "topic":
                recommendations.append(
                    f"Focus on {area['name']} - "
                    f"you answered {area['correct']}/{area['total']} correctly "
                    f"({area['percentage']:.0f}%)."
                )
            else:
                recommendations.append(
                    f"Practice more {area['name']} questions - "
                    f"you answered {area['correct']}/{area['total']} correctly "
                    f"({area['percentage']:.0f}%)."
                )

        # Get overall percentage safely
        overall_percentage = self.summary.get("percentage", 0.0)

        # Add one final overall recommendation
        if overall_percentage >= 90:
            recommendations.append(
                "Excellent performance. Try more advanced questions."
            )
        elif overall_percentage >= 70:
            recommendations.append(
                "Good job. Review incorrect answers to improve further."
            )
        elif overall_percentage >= 50:
            recommendations.append(
                "Keep practicing and focus on weaker topics."
            )
        else:
            recommendations.append(
                "Review the basics carefully and attempt the quiz again."
            )

        return recommendations

    # --------------------------------------------------
    # COMPLETE REPORT METHOD
    # --------------------------------------------------

    def get_complete_analysis(self) -> Dict[str, Any]:
        """
        Generate a complete report containing all analysis results.
        """

        # Compute topic and difficulty analysis once
        # so we do not repeat calculations unnecessarily
        topic_analysis = self.analyze_by_topic()
        difficulty_analysis = self.analyze_by_difficulty()

        # Find weak areas
        weak_areas = self.identify_weak_areas(
            topic_analysis=topic_analysis,
            difficulty_analysis=difficulty_analysis
        )

        # Find mastery levels
        mastery_levels = self.get_mastery_levels(
            topic_analysis=topic_analysis,
            difficulty_analysis=difficulty_analysis
        )

        # Find strongest area
        strongest_area = self.identify_strongest_area(
            topic_analysis=topic_analysis,
            difficulty_analysis=difficulty_analysis
        )

        # Generate recommendations
        recommendations = self.get_recommendations(
            weak_areas=weak_areas
        )

        # Return the final combined report
        return {
            "summary": {
                "score": self.summary.get("score", 0),
                "total_questions": self.summary.get("total_questions", 0),
                "percentage": self.summary.get("percentage", 0.0),
                "grade": self._calculate_grade(
                    self.summary.get("percentage", 0.0)
                )
            },
            "by_difficulty": difficulty_analysis,
            "by_topic": topic_analysis,
            "weak_areas": weak_areas,
            "strongest_area": strongest_area,
            "mastery_levels": mastery_levels,
            "recommendations": recommendations
        }
