import sys
import json
import re
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QComboBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QFileDialog,
    QMessageBox, QGroupBox, QDateTimeEdit, QGridLayout, QHeaderView, QAbstractItemView,
    QSlider, QSizePolicy, QStyle, QStyleOptionSlider, QStylePainter
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QFont, QPalette
import pandas as pd

# Define the log entry structure
class LogEntry:
    def __init__(self, timestamp=None, level=None, script=None, module=None, funcName=None, lineNo=None, message=None, **kwargs):
        # Handle timestamp
        if timestamp:
            try:
                self.timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                self.timestamp = None
        else:
            self.timestamp = None

        self.level = level
        self.script = script
        self.module = module
        self.funcName = funcName
        self.lineNo = lineNo
        self.message = message

        # Assign additional dynamic fields
        for key, value in kwargs.items():
            setattr(self, key, value)

    def matches(self, filters):
        for key, value in filters.items():
            if key == "timestamp":
                start, end = value
                if not (self.timestamp and start <= self.timestamp <= end):
                    return False
            elif key == "message":
                if not re.search(value, self.message, re.IGNORECASE):
                    return False
            else:
                # Handle case-insensitive comparison for string fields
                attr_value = getattr(self, key, "")
                if isinstance(attr_value, str) and isinstance(value, str):
                    if attr_value.lower() != value.lower():
                        return False
                else:
                    if attr_value != value:
                        return False
        return True

# Function to load logs from a file
def load_logs(file_path, start_line=0):
    logs = []
    try:
        with open(file_path, 'r') as f:
            # Skip lines up to start_line
            for _ in range(start_line):
                next(f, None)
            for line_number, line in enumerate(f, start=start_line + 1):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                try:
                    log_json = json.loads(line)

                    # Check for required fields
                    required_fields = ["timestamp", "level", "script", "module", "funcName", "lineNo", "message"]
                    if not all(field in log_json for field in required_fields):
                        missing = [field for field in required_fields if field not in log_json]
                        print(f"Missing fields {missing} on line {line_number}")
                        continue  # Skip this log entry

                    log_entry = LogEntry(**log_json)
                    logs.append(log_entry)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON on line {line_number}: {e}")
                except TypeError as e:
                    print(f"Error initializing LogEntry on line {line_number}: {e}")
    except FileNotFoundError:
        QMessageBox.critical(None, "File Not Found", f"File {file_path} not found.")
        sys.exit(1)
    return logs, start_line + len(logs)

# Signal emitter class for slider synchronization
class SliderSignals(QObject):
    start_slider_moved = pyqtSignal(int)
    end_slider_moved = pyqtSignal(int)

# Main GUI Application Class
class LogParserGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Log Parser")
        self.resize(1600, 900)  # Increased width for better slider visibility

        # Initialize data
        self.logs = []
        self.filtered_logs = []
        self.log_file_path = None
        self.last_line_count = 0
        self.poll_interval = 2000  # in milliseconds

        # Current filters
        self.current_filters_dict = {}

        # Initialize UI
        self.init_ui()

        # Start polling for new logs
        self.start_polling()

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Top buttons: Load, Reset, Export, Search
        button_layout = QHBoxLayout()

        load_button = QPushButton("Load Log File")
        load_button.clicked.connect(self.load_log_file)
        button_layout.addWidget(load_button)

        reset_button = QPushButton("Reset Filters")
        reset_button.clicked.connect(self.reset_filters)
        button_layout.addWidget(reset_button)

        export_button = QPushButton("Export Filtered Logs")
        export_button.clicked.connect(self.export_logs)
        button_layout.addWidget(export_button)

        # Search bar
        search_label = QLabel("Search:")
        button_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter search term...")
        self.search_edit.textChanged.connect(self.search_logs)
        button_layout.addWidget(self.search_edit)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Filter group box
        filter_group = QGroupBox("Filter Criteria")
        main_layout.addWidget(filter_group)
        filter_layout = QGridLayout()
        filter_group.setLayout(filter_layout)

        # Preset Filters - Span across 2 columns
        preset_label = QLabel("Quick Filters:")
        filter_layout.addWidget(preset_label, 0, 4, alignment=Qt.AlignRight)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom", "Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        filter_layout.addWidget(self.preset_combo, 0, 5)

        # Timeline Slider
        timeline_label = QLabel("Timeline Slider:")
        filter_layout.addWidget(timeline_label, 1, 0)

        self.timeline_slider_start = QSlider(Qt.Horizontal)
        self.timeline_slider_start.setMinimum(0)
        self.timeline_slider_start.setMaximum(100)
        self.timeline_slider_start.setValue(0)
        self.timeline_slider_start.setTickPosition(QSlider.TicksBelow)
        self.timeline_slider_start.setTickInterval(10)
        self.timeline_slider_start.valueChanged.connect(self.update_start_slider)

        self.timeline_slider_end = QSlider(Qt.Horizontal)
        self.timeline_slider_end.setMinimum(0)
        self.timeline_slider_end.setMaximum(100)
        self.timeline_slider_end.setValue(100)
        self.timeline_slider_end.setTickPosition(QSlider.TicksBelow)
        self.timeline_slider_end.setTickInterval(10)
        self.timeline_slider_end.valueChanged.connect(self.update_end_slider)

        # Labels to display selected dates
        self.timeline_start_label = QLabel("Start: Not Set")
        self.timeline_end_label = QLabel("End: Not Set")

        # Add sliders and labels to layout
        timeline_layout = QVBoxLayout()
        timeline_layout.addWidget(self.timeline_slider_start)
        timeline_layout.addWidget(self.timeline_start_label)
        timeline_layout.addWidget(self.timeline_slider_end)
        timeline_layout.addWidget(self.timeline_end_label)

        filter_layout.addLayout(timeline_layout, 1, 1, 1, 5)

        # Start DateTime - Combined with Timeline Slider
        # Removing separate date-time edits to focus on the timeline slider
        # Alternatively, you can keep both for more flexibility

        # Script Name
        script_label = QLabel("Script Name:")
        filter_layout.addWidget(script_label, 2, 0)

        self.script_edit = QLineEdit()
        self.script_edit.setPlaceholderText("Enter script name...")
        self.script_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_layout.addWidget(self.script_edit, 2, 1)

        # Module Name
        module_label = QLabel("Module Name:")
        filter_layout.addWidget(module_label, 2, 2)

        self.module_edit = QLineEdit()
        self.module_edit.setPlaceholderText("Enter module name...")
        self.module_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_layout.addWidget(self.module_edit, 2, 3)

        # Message Content
        message_label = QLabel("Message Content (Regex):")
        filter_layout.addWidget(message_label, 3, 0)

        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter regex for message content...")
        self.message_edit.setFixedHeight(80)  # Larger box for extensive input
        filter_layout.addWidget(self.message_edit, 3, 1, 1, 3)

        # Log Level
        level_label = QLabel("Log Level:")
        filter_layout.addWidget(level_label, 4, 0)

        self.level_combo = QComboBox()
        self.level_combo.addItem("")
        self.level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setFixedWidth(150)  # Smaller box for log levels
        filter_layout.addWidget(self.level_combo, 4, 1)

        # Apply Filters Button - Align to the right
        apply_filter_button = QPushButton("Apply Filters")
        apply_filter_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(apply_filter_button, 4, 5, alignment=Qt.AlignRight)

        # Set column stretch factors
        filter_layout.setColumnStretch(0, 1)  # Labels column
        filter_layout.setColumnStretch(1, 3)  # Primary input column
        filter_layout.setColumnStretch(2, 1)  # Secondary input column
        filter_layout.setColumnStretch(3, 1)  # Tertiary input column
        filter_layout.setColumnStretch(4, 1)  # Preset filters column
        filter_layout.setColumnStretch(5, 1)  # Preset filters column

        # Log display table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Level", "Script", "Module", "Function", "Line No", "Message"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(False)  # We'll handle row colors based on log levels
        main_layout.addWidget(self.table)

        # Set fonts and styles
        self.set_styles()

        # Initialize timeline range
        self.timeline_start_datetime = None
        self.timeline_end_datetime = None

    def set_styles(self):
        # Define color palette
        DARK_BLUE = "#04091E"          # Dark Blue
        TEAL_BLUE = "#027B8C"          # Muted Teal Blue
        CYAN_BLUE = "#008FBF"          # Muted Cyan Blue
        DARK_GREEN = "#228B22"         # Dark Green
        DARK_RED = "#B22222"           # Dark Red
        LIGHT_GRAY = "#D9E2EC"         # White/Light Gray
        ENTRY_BG = "#1C2B36"           # Slightly lighter than DARK_BLUE for contrast
        FRAME_BG = "#022B3A"           # Slightly different shade for frames
        BUTTON_ACTIVE_BG = "#025E73"   # Darker teal for active state
        TREEVIEW_BG = "#1C2B36"        # Background for Treeview
        TREEVIEW_TEXT = "#D9E2EC"      # Text color for Treeview
        TREEVIEW_HEADER_BG = TEAL_BLUE
        TREEVIEW_HEADER_FG = LIGHT_GRAY
        FONT = QFont("Segoe UI", 10)

        # Apply general palette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(DARK_BLUE))
        palette.setColor(QPalette.WindowText, QColor(LIGHT_GRAY))
        palette.setColor(QPalette.Base, QColor(ENTRY_BG))
        palette.setColor(QPalette.AlternateBase, QColor(FRAME_BG))
        palette.setColor(QPalette.Text, QColor(LIGHT_GRAY))
        palette.setColor(QPalette.Button, QColor(TEAL_BLUE))
        palette.setColor(QPalette.ButtonText, QColor(LIGHT_GRAY))
        palette.setColor(QPalette.Highlight, QColor(CYAN_BLUE))
        palette.setColor(QPalette.HighlightedText, QColor(LIGHT_GRAY))
        self.setPalette(palette)

        # Set font
        self.setFont(FONT)

        # Style Buttons
        button_style = """
            QPushButton {
                background-color: #027B8C;
                color: #D9E2EC;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #025E73;
            }
            QPushButton:pressed {
                background-color: #023F5C;
            }
        """
        self.setStyleSheet(button_style)

        # Style GroupBox
        groupbox_style = """
            QGroupBox {
                border: 1px solid #027B8C;
                margin-top: 10px;
                font-weight: bold;
                color: #D9E2EC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """
        self.findChild(QGroupBox).setStyleSheet(groupbox_style)

        # Style Labels
        label_style = """
            QLabel {
                color: #D9E2EC;
                font-weight: bold;
            }
        """
        for label in self.findChildren(QLabel):
            label.setStyleSheet(label_style)

        # Style LineEdits
        lineedit_style = """
            QLineEdit {
                background-color: #1C2B36;
                color: #D9E2EC;
                border: 1px solid #027B8C;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #008FBF;
            }
        """
        for lineedit in self.findChildren(QLineEdit):
            lineedit.setStyleSheet(lineedit_style)

        # Style ComboBoxes
        combobox_style = """
            QComboBox {
                background-color: #1C2B36;
                color: #D9E2EC;
                border: 1px solid #027B8C;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #1C2B36;
                color: #D9E2EC;
                selection-background-color: #008FBF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """
        for combobox in self.findChildren(QComboBox):
            combobox.setStyleSheet(combobox_style)

        # Style TextEdits
        textedit_style = """
            QTextEdit {
                background-color: #1C2B36;
                color: #D9E2EC;
                border: 1px solid #027B8C;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit:focus {
                border: 1px solid #008FBF;
            }
        """
        for textedit in self.findChildren(QTextEdit):
            textedit.setStyleSheet(textedit_style)

        # Style Sliders
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #1C2B36;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #027B8C;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -5px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal:hover {
                background: #025E73;
            }
            QSlider::handle:horizontal:pressed {
                background: #023F5C;
            }
        """
        for slider in self.findChildren(QSlider):
            slider.setStyleSheet(slider_style)

        # Style Table
        table_style = f"""
            QTableWidget {{
                background-color: {TREEVIEW_BG};
                color: {TREEVIEW_TEXT};
                gridline-color: #027B8C;
                border: 1px solid #027B8C;
            }}
            QHeaderView::section {{
                background-color: {TREEVIEW_HEADER_BG};
                color: {TREEVIEW_HEADER_FG};
                padding: 4px;
                border: 1px solid #027B8C;
            }}
            QTableWidget::item:selected {{
                background-color: {CYAN_BLUE};
                color: {LIGHT_GRAY};
            }}
        """
        self.table.setStyleSheet(table_style)

        # Set fonts for table
        self.table.setFont(FONT)
        self.table.horizontalHeader().setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table.verticalHeader().setVisible(False)

    def load_log_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "",
                                                   "Log Files (*.log *.ndjson);;All Files (*)", options=options)
        if file_path:
            self.log_file_path = file_path
            self.logs, self.last_line_count = load_logs(file_path)
            if not self.logs:
                QMessageBox.warning(self, "No Logs", "No valid log entries were found in the selected file.")
                return
            self.filtered_logs = self.logs.copy()
            self.display_logs(self.filtered_logs)
            QMessageBox.information(self, "Logs Loaded", f"Loaded {len(self.logs)} log entries.")

            # Initialize timeline range based on log timestamps
            timestamps = [log.timestamp for log in self.logs if log.timestamp]
            if timestamps:
                self.timeline_start_datetime = min(timestamps)
                self.timeline_end_datetime = max(timestamps)

                # Update timeline labels
                self.timeline_start_label.setText(f"Start: {self.timeline_start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                self.timeline_end_label.setText(f"End: {self.timeline_end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

                # Reset sliders
                self.timeline_slider_start.blockSignals(True)
                self.timeline_slider_end.blockSignals(True)
                self.timeline_slider_start.setValue(0)
                self.timeline_slider_end.setValue(100)
                self.timeline_slider_start.blockSignals(False)
                self.timeline_slider_end.blockSignals(False)

    def display_logs(self, logs):
        self.table.setRowCount(0)
        for log in logs:
            self.add_log_to_table(log)

    def add_log_to_table(self, log):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Timestamp
        if log.timestamp:
            timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = "Invalid Timestamp"
        self.table.setItem(row_position, 0, QTableWidgetItem(timestamp_str))

        # Level
        level_item = QTableWidgetItem(log.level if log.level else "")
        self.table.setItem(row_position, 1, level_item)

        # Script
        script_item = QTableWidgetItem(log.script if log.script else "")
        self.table.setItem(row_position, 2, script_item)

        # Module
        module_item = QTableWidgetItem(log.module if log.module else "")
        self.table.setItem(row_position, 3, module_item)

        # Function
        func_item = QTableWidgetItem(log.funcName if log.funcName else "")
        self.table.setItem(row_position, 4, func_item)

        # Line No
        line_item = QTableWidgetItem(str(log.lineNo) if log.lineNo else "")
        line_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row_position, 5, line_item)

        # Message
        message_item = QTableWidgetItem(log.message if log.message else "")
        self.table.setItem(row_position, 6, message_item)

        # Apply color based on log level
        if log.level:
            if log.level.upper() == "INFO":
                color = QColor("#1C2B36")  # Neutral
                text_color = QColor("#D9E2EC")
            elif log.level.upper() == "DEBUG":
                color = QColor("#1C2B36")  # Neutral
                text_color = QColor("#D9E2EC")
            elif log.level.upper() == "WARNING":
                color = QColor("#3A3F3F")  # Muted Yellow
                text_color = QColor("#D9E2EC")
            elif log.level.upper() in ["ERROR", "CRITICAL"]:
                color = QColor("#B22222")  # Dark Red
                text_color = QColor("#D9E2EC")
            else:
                color = QColor("#1C2B36")  # Default
                text_color = QColor("#D9E2EC")
        else:
            color = QColor("#1C2B36")  # Default
            text_color = QColor("#D9E2EC")

        for col in range(7):
            item = self.table.item(row_position, col)
            if item:
                item.setBackground(color)
                item.setForeground(text_color)

    def apply_filters(self):
        filters = {}

        # Timeline Slider Filters
        if self.timeline_start_datetime and self.timeline_end_datetime:
            start_percent = self.timeline_slider_start.value() / 100
            end_percent = self.timeline_slider_end.value() / 100

            # Prevent start from being after end
            if start_percent > end_percent:
                QMessageBox.warning(self, "Invalid Range", "Start slider cannot be after End slider.")
                return

            delta = self.timeline_end_datetime - self.timeline_start_datetime
            selected_start = self.timeline_start_datetime + delta * start_percent
            selected_end = self.timeline_start_datetime + delta * end_percent

            filters["timestamp"] = (selected_start, selected_end)

        # Script Filter
        script = self.script_edit.text().strip()
        if script:
            filters["script"] = script

        # Module Filter
        module = self.module_edit.text().strip()
        if module:
            filters["module"] = module

        # Message Content Filter
        message = self.message_edit.toPlainText().strip()
        if message:
            try:
                re.compile(message)  # Validate regex
                filters["message"] = message
            except re.error:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid regular expression for message content.")
                return

        # Log Level Filter
        level = self.level_combo.currentText().strip()
        if level:
            filters["level"] = level

        if not filters:
            self.filtered_logs = self.logs.copy()
            self.display_logs(self.filtered_logs)
            QMessageBox.information(self, "Filters Reset", "No filters applied. Displaying all logs.")
            return

        # Apply filters
        self.current_filters_dict = filters  # Update current filters
        self.filtered_logs = [log for log in self.logs if log.matches(filters)]
        self.display_logs(self.filtered_logs)
        QMessageBox.information(self, "Filters Applied", f"Found {len(self.filtered_logs)} matching log entries.")

    def reset_filters(self):
        # Reset timeline sliders to default values
        self.timeline_slider_start.blockSignals(True)
        self.timeline_slider_end.blockSignals(True)
        self.timeline_slider_start.setValue(0)
        self.timeline_slider_end.setValue(100)
        self.timeline_slider_start.blockSignals(False)
        self.timeline_slider_end.blockSignals(False)

        # Update timeline labels
        if self.timeline_start_datetime and self.timeline_end_datetime:
            self.timeline_start_label.setText(f"Start: {self.timeline_start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            self.timeline_end_label.setText(f"End: {self.timeline_end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        # Clear other filter inputs
        self.script_edit.clear()
        self.module_edit.clear()
        self.message_edit.clear()
        self.level_combo.setCurrentIndex(0)

        # Reset preset selection
        self.preset_combo.setCurrentText("Custom")

        # Reset filtered logs
        self.current_filters_dict = {}
        self.filtered_logs = self.logs.copy()
        self.display_logs(self.filtered_logs)
        QMessageBox.information(self, "Filters Reset", "All filters have been reset. Displaying all logs.")

    def export_logs(self):
        if not self.filtered_logs:
            QMessageBox.warning(self, "No Logs", "There are no logs to export.")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Logs", "",
                                                   "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)",
                                                   options=options)
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    # Prepare data for CSV
                    data = []
                    for log in self.filtered_logs:
                        log_dict = log.__dict__.copy()
                        if isinstance(log_dict.get("timestamp"), datetime):
                            log_dict["timestamp"] = log_dict["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        data.append(log_dict)
                    df = pd.DataFrame(data)
                    df.to_csv(file_path, index=False)
                elif file_path.endswith('.json'):
                    # Prepare data for JSON
                    data = []
                    for log in self.filtered_logs:
                        log_dict = log.__dict__.copy()
                        if isinstance(log_dict.get("timestamp"), datetime):
                            log_dict["timestamp"] = log_dict["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                        data.append(log_dict)
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                else:
                    QMessageBox.warning(self, "Unsupported Format", "Please choose either .csv or .json format for exporting.")
                    return
                QMessageBox.information(self, "Export Successful", f"Filtered logs exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting logs:\n{e}")

    def start_polling(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_logs)
        self.timer.start(self.poll_interval)

    def poll_logs(self):
        """Periodically check for new logs and update the display."""
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r') as f:
                    # Move to the last read position
                    for _ in range(self.last_line_count):
                        next(f, None)
                    new_logs, new_lines = load_logs(self.log_file_path, self.last_line_count)
                    if new_logs:
                        self.logs.extend(new_logs)
                        self.last_line_count += len(new_logs)
                        # Update timeline range if necessary
                        timestamps = [log.timestamp for log in new_logs if log.timestamp]
                        if timestamps:
                            new_start = min(timestamps)
                            new_end = max(timestamps)
                            if not self.timeline_start_datetime or new_start < self.timeline_start_datetime:
                                self.timeline_start_datetime = new_start
                            if not self.timeline_end_datetime or new_end > self.timeline_end_datetime:
                                self.timeline_end_datetime = new_end

                            # Update timeline labels
                            self.timeline_start_label.setText(f"Start: {self.timeline_start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                            self.timeline_end_label.setText(f"End: {self.timeline_end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

                        # Apply current filters to new logs
                        for log in new_logs:
                            if self.current_filters_dict:
                                if log.matches(self.current_filters_dict):
                                    self.filtered_logs.append(log)
                                    self.add_log_to_table(log)
                            else:
                                # If no filters, display all
                                self.filtered_logs.append(log)
                                self.add_log_to_table(log)
            except Exception as e:
                print(f"Error polling log file: {e}")

    def apply_preset(self, text):
        if text == "Last Hour":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(hours=1)
        elif text == "Last 24 Hours":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=1)
        elif text == "Last 7 Days":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=7)
        elif text == "Last 30 Days":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=30)
        else:
            # Custom selection
            return

        # Map the start and end datetime to slider values
        if self.timeline_start_datetime and self.timeline_end_datetime:
            total_delta = self.timeline_end_datetime - self.timeline_start_datetime
            if total_delta.total_seconds() <= 0:
                QMessageBox.warning(self, "Invalid Log Timestamps", "Log entries have invalid timestamps.")
                return

            start_percent = ((start_dt - self.timeline_start_datetime).total_seconds() / total_delta.total_seconds()) * 100
            end_percent = ((end_dt - self.timeline_start_datetime).total_seconds() / total_delta.total_seconds()) * 100

            # Clamp the values between 0 and 100
            start_percent = max(0, min(100, start_percent))
            end_percent = max(0, min(100, end_percent))

            # Block signals to prevent recursive updates
            self.timeline_slider_start.blockSignals(True)
            self.timeline_slider_end.blockSignals(True)

            self.timeline_slider_start.setValue(int(start_percent))
            self.timeline_slider_end.setValue(int(end_percent))

            self.timeline_slider_start.blockSignals(False)
            self.timeline_slider_end.blockSignals(False)

            # Update labels
            self.timeline_start_label.setText(f"Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            self.timeline_end_label.setText(f"End: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    def update_start_slider(self, value):
        if not self.timeline_start_datetime or not self.timeline_end_datetime:
            return

        start_percent = value / 100
        total_delta = self.timeline_end_datetime - self.timeline_start_datetime
        selected_start = self.timeline_start_datetime + timedelta(seconds=total_delta.total_seconds() * start_percent)

        # Update label
        self.timeline_start_label.setText(f"Start: {selected_start.strftime('%Y-%m-%d %H:%M:%S')}")

        # Ensure start slider does not exceed end slider
        if value > self.timeline_slider_end.value():
            self.timeline_slider_end.setValue(value)

    def update_end_slider(self, value):
        if not self.timeline_start_datetime or not self.timeline_end_datetime:
            return

        end_percent = value / 100
        total_delta = self.timeline_end_datetime - self.timeline_start_datetime
        selected_end = self.timeline_start_datetime + timedelta(seconds=total_delta.total_seconds() * end_percent)

        # Update label
        self.timeline_end_label.setText(f"End: {selected_end.strftime('%Y-%m-%d %H:%M:%S')}")

        # Ensure end slider is not less than start slider
        if value < self.timeline_slider_start.value():
            self.timeline_slider_start.setValue(value)

    def search_logs(self, text):
        if not text:
            self.display_logs(self.filtered_logs)
            return
        searched_logs = [log for log in self.filtered_logs if text.lower() in log.message.lower()]
        self.display_logs(searched_logs)

# Main function
def main():
    app = QApplication(sys.argv)
    gui = LogParserGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
