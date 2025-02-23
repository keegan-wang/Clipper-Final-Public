import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
import shutil

class VideoProcessorThread(QThread):
    progress = pyqtSignal(int)
    processingDone = pyqtSignal(str)  # Emit the output video path when done

    def __init__(self, scriptText, videoPaths):
        super().__init__()
        self.scriptText = scriptText
        self.videoPaths = videoPaths

    def run(self):
        try:
            script_path = "data/script/narration_script.txt"
            audio_path = "data/audio/narration_audio.mp3"
            input_folder = "data/clips"
            output_path = "outputs/final_video.mp4"

            # Save the script text to a file
            with open(script_path, "w") as script_file:
                script_file.write(self.scriptText)

            # Step 1: Generate AI narration
            self.progress.emit(10)
            subprocess.run(["python3", "src/scriptToTTS.py"], check=True)

            # Step 2: Detect objects in videos
            self.progress.emit(30)
            subprocess.run(["python3", "src/sceneDetection.py"], check=True)

            # Step 3: Match script to clips (if needed)
            self.progress.emit(60)
            subprocess.run(["python3", "src/scriptMatching.py"], check=True)

            # Step 4: Edit and export the final video
            self.progress.emit(80)
            subprocess.run(
                ["python3", "src/videoProcessing.py", script_path, audio_path, input_folder, output_path], check=True
            )

            # Emit final progress and signal processing completion
            self.progress.emit(100)
            self.processingDone.emit(output_path)

        except subprocess.CalledProcessError as e:
            print(f"Error during processing: {e}")


class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Video Processing App")
        self.resize(800, 600)

        # Layout and widgets
        layout = QVBoxLayout()

        self.scriptLabel = QLabel("Enter Script:")
        self.scriptTextEdit = QTextEdit()

        self.uploadButton = QPushButton("Upload Videos")
        self.uploadButton.clicked.connect(self.uploadVideos)

        self.startButton = QPushButton("Start Processing")
        self.startButton.clicked.connect(self.startProcessing)

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)

        self.outputLabel = QLabel("")
        self.playbackButton = QPushButton("Play Video")
        self.playbackButton.setVisible(False)
        self.playbackButton.clicked.connect(self.playVideo)

        # Video playback widget
        self.videoWidget = QVideoWidget()
        self.videoWidget.setVisible(False)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        # Add widgets to layout
        layout.addWidget(self.scriptLabel)
        layout.addWidget(self.scriptTextEdit)
        layout.addWidget(self.uploadButton)
        layout.addWidget(self.startButton)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.outputLabel)
        layout.addWidget(self.playbackButton)
        layout.addWidget(self.videoWidget)

        self.setLayout(layout)
        self.videoPaths = []
        self.outputVideoPath = ""

    def uploadVideos(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Clips", "", "Video Files (*.mp4 *.mov)")
        if files:
            self.videoPaths = files
            self.outputLabel.setText(f"Uploaded {len(files)} videos.")
    

        if files:
            # Step 1: Clear the `data/clips` folder
            clips_folder = "data/clips"
            if os.path.exists(clips_folder == False):
                os.makedirs(clips_folder, exist_ok=True)
            
            if os.path.exists(clips_folder):
                shutil.rmtree(clips_folder)  # Remove all files in the folder
                os.makedirs(clips_folder, exist_ok=True)

            # Step 2: Copy the uploaded files to `data/clips`
                self.videoPaths = []  # Reset the list of video paths
                for file_path in files:
                    destination = os.path.join(clips_folder, os.path.basename(file_path))
                    shutil.copy(file_path, destination)  # Copy the file
                    self.videoPaths.append(destination)  # Add the copied path to the list

            self.outputLabel.setText(f"Uploaded and stored {len(files)} videos.")
        else:
            self.outputLabel.setText("No videos selected.")


    def startProcessing(self):
        scriptText = self.scriptTextEdit.toPlainText().strip()
        if not scriptText or not self.videoPaths:
            self.outputLabel.setText("Please provide a script and upload videos.")
            return

        # Save the script text to a file
        script_path = "data/script/narration_script.txt"
        with open(script_path, "w") as script_file:
            script_file.write(scriptText)

        # Start the processing workflow
        self.processorThread = VideoProcessorThread(scriptText, self.videoPaths)
        self.processorThread.progress.connect(self.progressBar.setValue)
        self.processorThread.processingDone.connect(self.onProcessingDone)
        self.processorThread.start()


    def onProcessingDone(self, output_path):
        self.outputLabel.setText("Processing completed successfully!")
        self.progressBar.setValue(100)
        self.outputVideoPath = output_path
        self.playbackButton.setVisible(True)

    def playVideo(self):
        if not self.outputVideoPath:
            return

        self.videoWidget.setVisible(True)
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.outputVideoPath)))
        self.mediaPlayer.play()

    def closeEvent(self, event):
        self.cleanup_data()
        event.accept()
    def cleanup_data(self):
        folders_to_delete = ["data/clips", "data/metadata"]
        for folder in folders_to_delete:
            if os.path.exists(folder):
                shutil.rmtree(folder)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec_())



