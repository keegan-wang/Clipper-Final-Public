import sys
import os
import cv2
import torch
from ultralytics import YOLO
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QListWidget, QLineEdit, QTabWidget
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import numpy as np

# Load YOLOv8 model (pre-trained on COCO dataset)
YOLO_MODEL = YOLO('yolov8s.pt')  # Replace with your YOLOv8 model path if needed

class VideoAnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.video_metadata = {}  # Store video data (file path -> object detections by timestamp)
        self.current_frame_cache = {}  # Cache frames for display

    def initUI(self):
        layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Tab 1: Search Videos
        self.search_tab = QWidget()
        self.init_search_tab()
        self.tabs.addTab(self.search_tab, "Search Videos")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.setWindowTitle('Video Object Detection and Analysis App')
        self.resize(800, 600)

    def init_search_tab(self):
        layout = QVBoxLayout()

        # Upload and search buttons
        self.upload_button = QPushButton('Upload Videos')
        self.upload_button.clicked.connect(self.upload_videos)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Enter object to search for (e.g., car, person)')

        self.search_button = QPushButton('Search Videos')
        self.search_button.clicked.connect(self.search_videos)

        # Output label and results list
        self.search_status_label = QLabel('')
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_frame_for_timestamp)
        self.results_list.itemDoubleClicked.connect(self.open_video)

        # Frame display for timestamp preview
        self.frame_label = QLabel()
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label = QLabel('Frame Info:')

        # Add widgets to layout
        layout.addWidget(self.upload_button)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.search_status_label)
        layout.addWidget(self.results_list)
        layout.addWidget(self.frame_label)
        layout.addWidget(self.frame_info_label)

        self.search_tab.setLayout(layout)

    def upload_videos(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Select Videos', '', 'Video Files (*.mp4 *.avi *.mkv)')
        if files:
            self.search_status_label.setText('Processing videos...')
            QApplication.processEvents()

            for file in files:
                self.process_video(file)

            self.search_status_label.setText('Videos processed successfully!')

    def process_video(self, file_path):
        cap = cv2.VideoCapture(file_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        detected_objects = {}  # Track object durations
        all_detections = []  # Store every detection with its timestamp

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_count // fps

            if frame_count % (fps // 2) == 0:  # Analyze every 0.5 seconds
                results = YOLO_MODEL(frame)

                # Extract detected objects and their labels
                boxes = results[0].boxes
                object_classes = boxes.cls.cpu().numpy().astype(int)  # Class indices
                objects_in_frame = [results[0].names[class_idx] for class_idx in object_classes]

                # Track object durations and store every detection
                for obj in objects_in_frame:
                    all_detections.append((obj, timestamp))

                    if obj not in detected_objects:
                        detected_objects[obj] = {"start": timestamp, "duration": 0}

                    # Update duration if already detected
                    detected_objects[obj]["duration"] += 0.5

                # Cache the frame for display
                self.current_frame_cache[(file_path, timestamp)] = frame

            frame_count += 1

        cap.release()

        # Store all detections and objects meeting the 2-second threshold
        self.video_metadata[file_path] = {
            "all_detections": all_detections,
            "long_detections": {obj: data for obj, data in detected_objects.items() if data["duration"] >= 2}
        }

    def search_videos(self):
        self.results_list.clear()

        search_term = self.search_input.text().strip().lower()
        if not search_term:
            self.search_status_label.setText('Please enter a search term.')
            return

        results_found = False

        for file_path, data in self.video_metadata.items():
            all_detections = data["all_detections"]
            long_detections = data["long_detections"]

            # Show every instance of the object in the video
            for obj, timestamp in all_detections:
                if search_term in obj:
                    highlight = ""
                    if obj in long_detections and long_detections[obj]["start"] <= timestamp <= long_detections[obj]["start"] + long_detections[obj]["duration"]:
                        highlight = " (Visible for 2+ seconds)"

                    item_text = f'{os.path.basename(file_path)} - {obj} at {timestamp}s{highlight}'
                    self.results_list.addItem(item_text)
                    self.results_list.item(self.results_list.count() - 1).setData(Qt.UserRole, (file_path, timestamp))
                    results_found = True

        if not results_found:
            self.search_status_label.setText(f'No results found for "{search_term}".')
        else:
            self.search_status_label.setText(f'Search results for "{search_term}":')

    def show_frame_for_timestamp(self, item):
        file_path, timestamp = item.data(Qt.UserRole)

        if (file_path, timestamp) in self.current_frame_cache:
            frame = self.current_frame_cache[(file_path, timestamp)]

            # Convert the frame to QPixmap for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channels = frame_rgb.shape
            bytes_per_line = channels * width
            qimage = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.frame_label.setPixmap(pixmap)
            self.frame_info_label.setText(f'Frame Info: Timestamp = {timestamp}s')

        else:
            self.frame_info_label.setText('Frame not found in cache.')

    def open_video(self, item):
        file_path, _ = item.data(Qt.UserRole)
        os.system(f'open "{file_path}"')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoAnalyzerApp()
    window.show()
    sys.exit(app.exec_())
