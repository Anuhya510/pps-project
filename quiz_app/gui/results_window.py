# results_window.py
# Score Analyzer Module - Analyzes quiz results and provides performance insights

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for proper imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox,
    QComboBox, QTabWidget, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

# Define results file path (same as quiz_window.py)
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE_DIR / "data" / "quiz_results.json"


class ScoreAnalyzerGUI(QWidget):
    """
    Graphical user interface for analyzing quiz results.
    Provides insights on performance by topic, difficulty, and identifies weak areas.
    """
    
    def __init__(self):
        """Initialize the Score Analyzer GUI."""
        super().__init__()
        self.setWindowTitle("Score Analyzer - Performance Dashboard")
        self.resize(1100, 750)
        self.all_quizzes = []
        self.current_quiz = None
        self._build_ui()
        self._auto_load_results()

    def _build_ui(self):
        """Build the user interface layout."""
        main_layout = QVBoxLayout(self)

        # Top section - Quiz Selector and Controls
        top_section = QGroupBox("Quiz Selection & Controls")
        top_layout = QVBoxLayout(top_section)
        
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Select Quiz:"))
        
        self.quiz_selector = QComboBox()
        self.quiz_selector.setMinimumWidth(450)
        self.quiz_selector.currentIndexChanged.connect(self.on_quiz_selected)
        selector_row.addWidget(self.quiz_selector)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._auto_load_results)
        selector_row.addWidget(self.refresh_btn)
        
        self.load_btn = QPushButton("Load JSON File")
        self.load_btn.clicked.connect(self.load_json)
        selector_row.addWidget(self.load_btn)
        
        top_layout.addLayout(selector_row)
        
        # Info label
        self.info_label = QLabel("Select a quiz from the dropdown or click 'Load JSON File' to load results.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #555; padding: 5px;")
        top_layout.addWidget(self.info_label)
        
        main_layout.addWidget(top_section)

        # Summary Section - Overall Performance
        summary_section = QGroupBox("Performance Summary")
        summary_layout = QVBoxLayout(summary_section)
        
        self.summary_text = QLabel("No quiz loaded. Please select or load a quiz.")
        self.summary_text.setWordWrap(True)
        self.summary_text.setStyleSheet("font-size: 12pt; padding: 10px; background-color: #f8f9fa;")
        summary_layout.addWidget(self.summary_text)
        
        main_layout.addWidget(summary_section)

        # Tab Widget for different analysis views
        self.tab_widget = QTabWidget()
        
        # Tab 1: Topic Performance
        self.topic_tab = self._create_topic_tab()
        self.tab_widget.addTab(self.topic_tab, "By Topic")
        
        # Tab 2: Difficulty Performance
        self.difficulty_tab = self._create_difficulty_tab()
        self.tab_widget.addTab(self.difficulty_tab, "By Difficulty")
        
        # Tab 3: Mastery & Recommendations
        self.mastery_tab = self._create_mastery_tab()
        self.tab_widget.addTab(self.mastery_tab, "Mastery & Recommendations")
        
        # Tab 4: Detailed Answers
        self.detailed_tab = self._create_detailed_tab()
        self.tab_widget.addTab(self.detailed_tab, "Detailed Answers")
        
        main_layout.addWidget(self.tab_widget)

    def _create_topic_tab(self):
        """Create the topic performance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.topic_table = QTableWidget(0, 5)
        self.topic_table.setHorizontalHeaderLabels(["Topic", "Correct", "Total", "Percentage", "Status"])
        self.topic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.topic_table.setAlternatingRowColors(True)
        layout.addWidget(self.topic_table)
        
        return widget

    def _create_difficulty_tab(self):
        """Create the difficulty performance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.difficulty_table = QTableWidget(0, 5)
        self.difficulty_table.setHorizontalHeaderLabels(["Difficulty", "Correct", "Total", "Percentage", "Status"])
        self.difficulty_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.difficulty_table.setAlternatingRowColors(True)
        layout.addWidget(self.difficulty_table)
        
        return widget

    def _create_mastery_tab(self):
        """Create the mastery levels and recommendations tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Mastery levels section
        mastery_group = QGroupBox("Mastery Levels")
        mastery_layout = QVBoxLayout(mastery_group)
        self.mastery_text = QTextEdit()
        self.mastery_text.setReadOnly(True)
        self.mastery_text.setMaximumHeight(180)
        mastery_layout.addWidget(self.mastery_text)
        layout.addWidget(mastery_group)
        
        # Weak areas section
        weak_group = QGroupBox("Weak Areas (Needs Improvement)")
        weak_layout = QVBoxLayout(weak_group)
        self.weak_text = QTextEdit()
        self.weak_text.setReadOnly(True)
        weak_layout.addWidget(self.weak_text)
        layout.addWidget(weak_group)
        
        # Recommendations section
        reco_group = QGroupBox("Recommendations")
        reco_layout = QVBoxLayout(reco_group)
        self.reco_text = QTextEdit()
        self.reco_text.setReadOnly(True)
        reco_layout.addWidget(self.reco_text)
        layout.addWidget(reco_group)
        
        return widget

    def _create_detailed_tab(self):
        """Create the detailed answers tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.detailed_table = QTableWidget(0, 5)
        self.detailed_table.setHorizontalHeaderLabels(["Q#", "Question", "Your Answer", "Correct Answer", "Result"])
        self.detailed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.detailed_table.setAlternatingRowColors(True)
        layout.addWidget(self.detailed_table)
        
        return widget

    def _auto_load_results(self):
        """Automatically load results from the default results file."""
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                
                # Handle different data structures
                if isinstance(data, list):
                    self.all_quizzes = data
                elif isinstance(data, dict):
                    self.all_quizzes = [data]
                else:
                    self.all_quizzes = []
                
                # Clear and repopulate the quiz selector
                self.quiz_selector.clear()
                self.quiz_selector.addItem("-- Select a Quiz to Analyze --")
                
                if self.all_quizzes:
                    # Show quizzes in reverse order (newest first)
                    for idx, quiz in enumerate(reversed(self.all_quizzes), 1):
                        date = quiz.get('date', 'Unknown')
                        score = quiz.get('score', 0)
                        total = quiz.get('total', 0)
                        percentage = quiz.get('percentage', 0)
                        # Handle missing student_name - use "Unknown" as fallback
                        student_name = quiz.get('student_name', 'Unknown')
                        self.quiz_selector.addItem(f"Quiz #{idx} - {student_name} | {date} | Score: {score}/{total} ({percentage:.1f}%)")
                    
                    self.info_label.setText(f"Loaded {len(self.all_quizzes)} quiz results. Select a quiz to analyze.")
                else:
                    self.info_label.setText("No quiz results found. Take a quiz first.")
                    
            except json.JSONDecodeError as e:
                self.info_label.setText(f"Error parsing JSON file: {e}")
                self.all_quizzes = []
            except Exception as e:
                self.info_label.setText(f"Error loading results: {e}")
                self.all_quizzes = []
        else:
            self.info_label.setText(f"No results file found. Please take a quiz first to generate results.")
            self.all_quizzes = []

    def on_quiz_selected(self, index):
        """Handle quiz selection from dropdown."""
        if index > 0 and self.all_quizzes:
            # Get selected quiz (accounting for reversed order)
            selected_idx = len(self.all_quizzes) - index
            if 0 <= selected_idx < len(self.all_quizzes):
                self.current_quiz = self.all_quizzes[selected_idx]
                self._analyze_current_quiz()
        else:
            self.current_quiz = None
            self._clear_all()

    def _analyze_current_quiz(self):
        """Analyze the currently selected quiz and update all displays."""
        if not self.current_quiz:
            return
        
        quiz = self.current_quiz
        answers = quiz.get('answers', [])
        score = quiz.get('score', 0)
        total = quiz.get('total', 0)
        percentage = quiz.get('percentage', 0)
        date = quiz.get('date', 'Unknown')
        # Handle missing student_name - use "Unknown" as fallback
        student_name = quiz.get('student_name', 'Unknown')
        
        # Update summary with student name
        grade = self._get_grade(percentage)
        summary_html = f"""
        <b>Student Name:</b> {student_name}<br>
        <b>Quiz Date:</b> {date}<br>
        <b>Score:</b> {score} / {total}<br>
        <b>Percentage:</b> {percentage:.1f}%<br>
        <b>Grade:</b> {grade}<br>
        <b>Status:</b> {'Excellent! Keep it up!' if percentage >= 80 else 'Good effort. Review the weak areas.' if percentage >= 60 else 'Needs improvement. Please review the material.'}
        """
        self.summary_text.setText(summary_html)
        
        # Analyze by topic
        topic_stats = self._calculate_by_topic(answers)
        self._populate_topic_table(topic_stats)
        
        # Analyze by difficulty
        difficulty_stats = self._calculate_by_difficulty(answers)
        self._populate_difficulty_table(difficulty_stats)
        
        # Mastery levels and recommendations
        self._update_mastery_tab(topic_stats, difficulty_stats, percentage)
        
        # Detailed answers
        self._populate_detailed_table(answers)

    def _calculate_by_topic(self, answers):
        """Calculate statistics by topic."""
        topic_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            topic = answer.get('topic', 'General')
            is_correct = answer.get('is_correct', False)
            topic_stats[topic]['total'] += 1
            if is_correct:
                topic_stats[topic]['correct'] += 1
        
        # Calculate percentages
        for topic in topic_stats:
            total = topic_stats[topic]['total']
            correct = topic_stats[topic]['correct']
            topic_stats[topic]['percentage'] = (correct / total * 100) if total > 0 else 0
        
        return dict(topic_stats)

    def _calculate_by_difficulty(self, answers):
        """Calculate statistics by difficulty."""
        diff_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for answer in answers:
            difficulty = answer.get('difficulty', 'medium')
            is_correct = answer.get('is_correct', False)
            diff_stats[difficulty]['total'] += 1
            if is_correct:
                diff_stats[difficulty]['correct'] += 1
        
        # Calculate percentages
        for diff in diff_stats:
            total = diff_stats[diff]['total']
            correct = diff_stats[diff]['correct']
            diff_stats[diff]['percentage'] = (correct / total * 100) if total > 0 else 0
        
        return dict(diff_stats)

    def _populate_topic_table(self, topic_stats):
        """Populate the topic performance table."""
        self.topic_table.setRowCount(0)
        
        for topic, stats in sorted(topic_stats.items()):
            row = self.topic_table.rowCount()
            self.topic_table.insertRow(row)
            
            self.topic_table.setItem(row, 0, QTableWidgetItem(topic))
            self.topic_table.setItem(row, 1, QTableWidgetItem(str(stats['correct'])))
            self.topic_table.setItem(row, 2, QTableWidgetItem(str(stats['total'])))
            
            percentage = stats['percentage']
            percent_item = QTableWidgetItem(f"{percentage:.1f}%")
            self._color_percentage_item(percent_item, percentage)
            self.topic_table.setItem(row, 3, percent_item)
            
            status_item = QTableWidgetItem(self._get_status_text(percentage))
            self._color_status_item(status_item, percentage)
            self.topic_table.setItem(row, 4, status_item)
        
        self.topic_table.resizeColumnsToContents()

    def _populate_difficulty_table(self, difficulty_stats):
        """Populate the difficulty performance table."""
        self.difficulty_table.setRowCount(0)
        
        difficulty_order = {'easy': 0, 'medium': 1, 'hard': 2}
        for diff in sorted(difficulty_stats.keys(), key=lambda x: difficulty_order.get(x, 3)):
            stats = difficulty_stats[diff]
            row = self.difficulty_table.rowCount()
            self.difficulty_table.insertRow(row)
            
            self.difficulty_table.setItem(row, 0, QTableWidgetItem(diff.capitalize()))
            self.difficulty_table.setItem(row, 1, QTableWidgetItem(str(stats['correct'])))
            self.difficulty_table.setItem(row, 2, QTableWidgetItem(str(stats['total'])))
            
            percentage = stats['percentage']
            percent_item = QTableWidgetItem(f"{percentage:.1f}%")
            self._color_percentage_item(percent_item, percentage)
            self.difficulty_table.setItem(row, 3, percent_item)
            
            status_item = QTableWidgetItem(self._get_status_text(percentage))
            self._color_status_item(status_item, percentage)
            self.difficulty_table.setItem(row, 4, status_item)
        
        self.difficulty_table.resizeColumnsToContents()

    def _populate_detailed_table(self, answers):
        """Populate the detailed answers table."""
        self.detailed_table.setRowCount(0)
        
        for idx, answer in enumerate(answers, 1):
            row = self.detailed_table.rowCount()
            self.detailed_table.insertRow(row)
            
            self.detailed_table.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.detailed_table.setItem(row, 1, QTableWidgetItem(answer.get('question', 'Unknown')[:80]))
            self.detailed_table.setItem(row, 2, QTableWidgetItem(answer.get('selected_option', 'N/A')))
            self.detailed_table.setItem(row, 3, QTableWidgetItem(answer.get('correct_option', 'N/A')))
            
            is_correct = answer.get('is_correct', False)
            result_item = QTableWidgetItem("Correct" if is_correct else "Incorrect")
            result_item.setForeground(QBrush(QColor("#27ae60") if is_correct else QColor("#e74c3c")))
            self.detailed_table.setItem(row, 4, result_item)
        
        self.detailed_table.resizeColumnsToContents()

    def _update_mastery_tab(self, topic_stats, difficulty_stats, overall_percentage):
        """Update the mastery levels and recommendations tab."""
        # Mastery levels text
        mastery_text = f"""
        <b>Overall Mastery Level:</b><br>
        Score: {overall_percentage:.1f}% - {self._get_mastery_level(overall_percentage)}<br>
        <br>
        <b>Topic-wise Mastery:</b><br>
        """
        for topic, stats in sorted(topic_stats.items()):
            mastery_text += f"• {topic}: {stats['percentage']:.1f}% ({self._get_mastery_level(stats['percentage'])})\n"
        
        self.mastery_text.setText(mastery_text)
        
        # Weak areas (topics with < 60% score)
        weak_text = ""
        weak_topics = [(t, s) for t, s in topic_stats.items() if s['percentage'] < 60]
        if weak_topics:
            weak_text = "Topics that need improvement:\n\n"
            for topic, stats in sorted(weak_topics, key=lambda x: x[1]['percentage']):
                weak_text += f"• {topic}: {stats['correct']}/{stats['total']} correct ({stats['percentage']:.1f}%)\n"
        else:
            weak_text = "No weak areas identified! Great job!"
        
        self.weak_text.setText(weak_text)
        
        # Recommendations
        recommendations = []
        if overall_percentage < 60:
            recommendations.append("Review fundamental concepts before attempting more quizzes.")
        elif overall_percentage < 80:
            recommendations.append("Good progress! Focus on practicing weak areas identified above.")
        else:
            recommendations.append("Excellent performance! Try attempting harder difficulty questions.")
        
        for topic, stats in weak_topics:
            recommendations.append(f"Review {topic} - you got {stats['correct']}/{stats['total']} correct.")
        
        # Difficulty-based recommendations
        for diff, stats in difficulty_stats.items():
            if stats['percentage'] < 60:
                recommendations.append(f"Practice more {diff} level questions.")
        
        if not recommendations:
            recommendations.append("Keep practicing to maintain your performance level.")
        
        self.reco_text.setText("\n\n".join(recommendations))

    def _get_mastery_level(self, percentage):
        """Get mastery level text."""
        if percentage >= 90:
            return "Mastery"
        elif percentage >= 75:
            return "Proficient"
        elif percentage >= 60:
            return "Developing"
        elif percentage >= 40:
            return "Beginner"
        else:
            return "Needs Work"

    def _get_grade(self, percentage):
        """Get letter grade."""
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B"
        elif percentage >= 60:
            return "C"
        elif percentage >= 50:
            return "D"
        else:
            return "F"

    def _get_status_text(self, percentage):
        """Get status text based on percentage."""
        if percentage >= 80:
            return "Strong"
        elif percentage >= 60:
            return "Satisfactory"
        elif percentage >= 40:
            return "Needs Work"
        else:
            return "Weak"

    def _color_percentage_item(self, item, percentage):
        """Color a percentage table item based on value."""
        if percentage >= 80:
            item.setForeground(QBrush(QColor("#27ae60")))
        elif percentage >= 60:
            item.setForeground(QBrush(QColor("#f39c12")))
        else:
            item.setForeground(QBrush(QColor("#e74c3c")))

    def _color_status_item(self, item, percentage):
        """Color a status table item based on value."""
        if percentage >= 80:
            item.setForeground(QBrush(QColor("#27ae60")))
            item.setBackground(QBrush(QColor("#d5f5e3")))
        elif percentage >= 60:
            item.setForeground(QBrush(QColor("#f39c12")))
            item.setBackground(QBrush(QColor("#fef9e7")))
        else:
            item.setForeground(QBrush(QColor("#e74c3c")))
            item.setBackground(QBrush(QColor("#fadbd8")))

    def load_json(self):
        """Load quiz results from an external JSON file selected by the user."""
        # Start from the data directory
        start_dir = str(BASE_DIR / "data")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Quiz Results JSON", 
            start_dir, 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # Handle different JSON structures
            if isinstance(data, list):
                self.all_quizzes = data
            elif isinstance(data, dict):
                if 'answers' in data or 'score' in data:
                    self.all_quizzes = [data]
                else:
                    self.all_quizzes = [data]
            else:
                raise ValueError("Invalid JSON format. Expected an object or array.")
            
            # Populate quiz selector with student name
            self.quiz_selector.clear()
            self.quiz_selector.addItem("-- Select a Quiz to Analyze --")
            
            for idx, quiz in enumerate(reversed(self.all_quizzes), 1):
                date = quiz.get('date', 'Unknown')
                score = quiz.get('score', 0)
                total = quiz.get('total', 0)
                percentage = quiz.get('percentage', 0)
                student_name = quiz.get('student_name', 'Unknown')
                self.quiz_selector.addItem(f"Quiz #{idx} - {student_name} | {date} | Score: {score}/{total} ({percentage:.1f}%)")
            
            self.info_label.setText(f"Loaded {len(self.all_quizzes)} quizzes from: {Path(file_path).name}")
            
        except json.JSONDecodeError as error:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON file: {error}")
        except Exception as error:
            QMessageBox.critical(self, "Error", f"Failed to load file: {error}")

    def _clear_all(self):
        """Clear all UI displays."""
        self.topic_table.setRowCount(0)
        self.difficulty_table.setRowCount(0)
        self.detailed_table.setRowCount(0)
        self.mastery_text.clear()
        self.weak_text.clear()
        self.reco_text.clear()
        self.summary_text.setText("No quiz selected. Select a quiz from the dropdown above.")


def main():
    """Main entry point for the Score Analyzer application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = ScoreAnalyzerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()