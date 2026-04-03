# score_analyzer_gui.py
import sys
import json
from pathlib import Path
from typing import Dict, Any

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt

# Adjust import path if necessary
from score_analyzer import ScoreAnalyzer  # file that contains your ScoreAnalyzer class

class ScoreAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Score Analyzer")
        self.resize(900, 600)
        self.analyzer = None
        self.results = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.load_btn = QPushButton("Load results JSON")
        self.load_btn.clicked.connect(self.load_json)
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setEnabled(False)
        top_row.addWidget(self.load_btn)
        top_row.addWidget(self.analyze_btn)
        main.addLayout(top_row)

        # Summary box
        summary_box = QGroupBox("Summary")
        s_layout = QHBoxLayout()
        self.summary_label = QLabel("No data loaded")
        s_layout.addWidget(self.summary_label)
        summary_box.setLayout(s_layout)
        main.addWidget(summary_box)

        # Tables: by topic and by difficulty
        tables_row = QHBoxLayout()
        self.topic_table = QTableWidget(0, 4)
        self.topic_table.setHorizontalHeaderLabels(["Topic", "Correct", "Total", "Percentage"])
        self.difficulty_table = QTableWidget(0, 4)
        self.difficulty_table.setHorizontalHeaderLabels(["Difficulty", "Correct", "Total", "Percentage"])
        tables_row.addWidget(self._wrap_group("By Topic", self.topic_table))
        tables_row.addWidget(self._wrap_group("By Difficulty", self.difficulty_table))
        main.addLayout(tables_row)

        # Weak areas and mastery + recommendations
        bottom_row = QHBoxLayout()

        self.weak_text = QTextEdit()
        self.weak_text.setReadOnly(True)
        bottom_row.addWidget(self._wrap_group("Weak Areas", self.weak_text))

        right_col = QVBoxLayout()
        self.mastery_text = QTextEdit(); self.mastery_text.setReadOnly(True)
        self.reco_text = QTextEdit(); self.reco_text.setReadOnly(True)
        right_col.addWidget(self._wrap_group("Mastery Levels", self.mastery_text))
        right_col.addWidget(self._wrap_group("Recommendations", self.reco_text))

        bottom_row.addLayout(right_col)
        main.addLayout(bottom_row)

    def _wrap_group(self, title: str, widget):
        g = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        g.setLayout(layout)
        return g

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open results JSON", str(Path.cwd()), "JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.results = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")
            return

        self.summary_label.setText(f"Loaded: {Path(path).name}")
        self.analyze_btn.setEnabled(True)
        # Clear previous UI
        self._clear_ui()

    def analyze(self):
        if not self.results:
            QMessageBox.warning(self, "No data", "Load a results JSON first.")
            return

        try:
            self.analyzer = ScoreAnalyzer(self.results)  # ScoreAnalyzer must accept results in ctor
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analyzer init failed: {e}")
            return

        report = self.analyzer.get_complete_analysis()

        # Summary
        s = report["summary"]
        self.summary_label.setText(
            f"Score: {s['score']} / {s['total_questions']}  ({s['percentage']}%)  Grade: {s['grade']}"
        )

        # Populate tables
        self._populate_table(self.topic_table, report["by_topic"])
        self._populate_table(self.difficulty_table, report["by_difficulty"])

        # Weak areas
        wa_text = ""
        for w in report["weak_areas"]:
            wa_text += f"{w['type'].title()}: {w['name']} — {w['correct']}/{w['total']} ({w['percentage']}%)\n  Rec: {w['recommendation']}\n\n"
        self.weak_text.setPlainText(wa_text or "None")

        # Mastery
        mastery_lines = [f"{k}: {v}" for k, v in report["mastery_levels"].items()]
        self.mastery_text.setPlainText("\n".join(mastery_lines) or "None")

        # Recommendations
        self.reco_text.setPlainText("\n".join(report["recommendations"]) or "None")

    def _populate_table(self, table: QTableWidget, data: Dict[str, Dict[str, Any]]):
        table.setRowCount(0)
        for key, vals in data.items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(key)))
            table.setItem(row, 1, QTableWidgetItem(str(vals.get("correct", 0))))
            table.setItem(row, 2, QTableWidgetItem(str(vals.get("total", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(vals.get("percentage", 0.0))))

        table.resizeColumnsToContents()

    def _clear_ui(self):
        self.topic_table.setRowCount(0)
        self.difficulty_table.setRowCount(0)
        self.weak_text.clear()
        self.mastery_text.clear()
        self.reco_text.clear()

def main():
    app = QApplication(sys.argv)
    w = ScoreAnalyzerGUI()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
