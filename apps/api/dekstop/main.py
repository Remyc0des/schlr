import sys
import random
from PySide6 import QtWidgets
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QLineEdit,
)
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))


from src.courses.course import Course
from src.lecture_ai.audio.record import AudioRecorder
from src.lecture_ai.audio.segmentation import Transcriber
from src.lecture_ai.lecture import MyLecture

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LectureAI")
        self.resize(1000, 650)

        # Root widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout: sidebar | content
        main_layout = QHBoxLayout(central)


        ## courses code
        self.courses = []

        # -------------------------
        # Sidebar
        # -------------------------

        sidebar = QFrame()
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)

        courses_label = QLabel("COURSES")
        sidebar_layout.addWidget(courses_label)

        self.course_list = QListWidget()
        self.course_list.addItems([
        ])

        sidebar_layout.addWidget(self.course_list)
        self.course_list.itemClicked.connect(self.open_course)

        new_course_button = QPushButton("+ Course")
        sidebar_layout.addWidget(new_course_button)
        new_course_button.clicked.connect(self.add_course)

        sidebar_layout.addStretch()

        # -------------------------
        # Main content
        # -------------------------

        content = QWidget()
        
        content_layout = QVBoxLayout(content)
        self.content_layout = content_layout 
        welcome = QLabel("Welcome back")
        welcome.setObjectName("welcome")

        subtitle = QLabel("Your courses")

        content_layout.addWidget(welcome)
        content_layout.addWidget(subtitle)

        # New lecture button
        new_lecture_button = QPushButton("+ New Lecture")
        new_lecture_button.setFixedSize(180, 50)
        new_lecture_button.clicked.connect(lambda: self.record_lecture(None))  # No course selected yet

        content_layout.addWidget(new_lecture_button)

        content_layout.addSpacing(30)

        # Recent lectures
        recent_label = QLabel("Recent lectures")
        content_layout.addWidget(recent_label)

        lectures = QListWidget()
        lectures.addItems([
            "Calculus — Oct 2",
            "Data Structures — Oct 1",
        ])

        content_layout.addWidget(lectures)

        content_layout.addStretch()

        # Put sidebar + content together
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)


        ## course page
        self.course_page = QWidget()
        course_page_layout = QVBoxLayout(self.course_page)

        course_title = QLabel("Course Title")
        course_title.setObjectName("course_title")

        course_page_layout.addWidget(course_title)

        new_lecture_button = QPushButton("+ New Lecture")
        new_lecture_button.setFixedSize(180, 50)
        
        self.timer_label = QLabel("00:00:00")

        self.status_label = QLabel("Ready")

        self.record_button = QPushButton("● Record")
        self.stop_button = QPushButton("■ Stop")
        self.stop_button.setEnabled(False)

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        course_page_layout.addWidget(new_lecture_button)
        
        course_page_layout.addSpacing(30)
        
                # Recent lectures
        lec_label = QLabel(" lectures")
        course_page_layout.addWidget(lec_label)
        
        lectures = QListWidget()
        lectures.addItems([
                "Calculus — Oct 2",
                "Data Structures — Oct 1",
            ])
        
        course_page_layout.addWidget(lectures)
        
        course_page_layout.addStretch()

        course_page_layout.addWidget(course_title)

        self.transcriber = Transcriber() 
        self.recorder = AudioRecorder(on_chunk=self.transcriber.feed)  

        #self.content_layout.addWidget(title)
        

        # -------------------------
        # Basic styling
        # -------------------------

        self.setStyleSheet("""
            QMainWindow {
                background: #f7f7f7;
            }

            QLabel {
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#welcome {
                font-size: 32px;
                font-weight: bold;
            }
            QLabel#title {
                            font-size: 32px;
                            font-weight: bold;
                        }

            QListWidget {
                background: white;
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 5px;
            }

            QPushButton {
                padding: 10px;
                border-radius: 8px;
            }
        """)

    ## add courses
    def add_course(self):
        name, ok = QInputDialog.getText(self, "New Course", "Enter course name:")
        if ok and name.strip():
            course = Course(name.strip())
            self.courses.append(course)
            item = QListWidgetItem(course.name)
            item.setData(QtCore.Qt.UserRole, course)
            self.course_list.addItem(item)
            print(f"Added course: {course.name}")

    def open_course(self, item):
        course = item.data(QtCore.Qt.UserRole)

    # Remove whatever is currently in the content area
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    # Build course page
        title = QLabel(course.name)
        self.content_layout.addWidget(title)

        new_lecture_button = QPushButton("+ New Lecture")
        recent_label = QLabel("Recent lectures")
        self.content_layout.addWidget(recent_label)

        self.content_layout.addWidget(new_lecture_button)
        
        lectures = QListWidget()
        lectures.addItems([
            "Calculus — Oct 2",
            "Data Structures — Oct 1",
            ])
        
        self.content_layout.addWidget(lectures)
        
        self.content_layout.addStretch()

        self.content_layout.addStretch()

    def record_lecture(self, course):

        # ----- Main recording area -----

        title = QLabel("Lecture Recording")
        title.setObjectName("course_title")

        # Live transcript
        transcript_label = QLabel("Live transcript")

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("Your live transcript will appear here...")

        # ----- Bottom recording bar -----

        recording_bar = QFrame()
        recording_bar.setObjectName("recording_bar")
        recording_bar.setFixedHeight(100)

        recording_layout = QHBoxLayout(recording_bar)

        self.statusLabel = QLabel("Ready to record...")
        self.timer_label = QLabel("00:00:00")

        self.record_button = QPushButton("● Record")

        self.stop_button = QPushButton("■ Stop")
        self.stop_button.setEnabled(False)

        # Temporary waveform
        self.waveform = QLabel("〰〰〰〰〰〰〰〰〰〰〰")
        self.waveform.setObjectName("waveform")

        # Recording bar layout
        recording_layout.addWidget(self.statusLabel)
        recording_layout.addSpacing(20)
        recording_layout.addWidget(self.timer_label)
        recording_layout.addStretch()
        recording_layout.addWidget(self.waveform)
        recording_layout.addStretch()
        recording_layout.addWidget(self.record_button)
        recording_layout.addWidget(self.stop_button)

        # ----- Add everything to the main content -----

        self.content_layout.addWidget(title)
        self.content_layout.addWidget(transcript_label)

        # Give transcript most of the available space
        self.content_layout.addWidget(self.transcript, 1)

        # Recording controls stay at the bottom
        self.content_layout.addWidget(recording_bar)

        # ----- Buttons -----

        self.record_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)

        
        #
    def start_recording(self):
        self.transcriber.start()
        self.recorder.record()

        self.status_label.setText("● Recording")
        self.record_button.setEnabled(False)
        self.stop_button.setEnabled(True)


    def stop_recording(self):
        audio = self.recorder.stop()
        text = self.transcriber.stop()
        self.status_label.setText("Recording saved")
        self.record_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())