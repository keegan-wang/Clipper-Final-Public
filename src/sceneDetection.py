import os
import json
import cv2
import shutil
from ultralytics import YOLO

yolo = YOLO('yolov8s.pt')

def delete_old_metadata(output_folder):
    """Delete all old metadata files from the output folder."""
    if os.path.exists(output_folder):
        print("Deleting old metadata...")
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    print("Metadata folder has been cleared.")


def detect_objects_in_clips(clips_folder, output_folder):
    """Analyze all video clips in the clips folder and generate metadata."""
    for filename in os.listdir(clips_folder):
        if filename.endswith((".mp4", ".mov")):
            video_path = os.path.join(clips_folder, filename)
            print(f"Starting analysis for {filename}...")

            # Open the video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file {filename}")
                continue

            # Get frames per second (FPS)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if fps == 0:
                print(f"Error: FPS is 0 for video {filename}. Skipping...")
                cap.release()
                continue

            # Analyze video frames
            metadata = []
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print(f"End of video reached for {filename}")
                    break

                if frame_count % fps == 0:  # Analyze one frame per second
                    results = yolo(frame)
                    detected_objects = [results[0].names[int(cls)] for cls in results[0].boxes.cls.cpu().numpy()]
                    metadata.append({"timestamp": frame_count // fps, "objects": detected_objects})

                frame_count += 1

            cap.release()
            print(f"Finished analysis for {filename}. Frames analyzed: {frame_count // fps}")

            # Save metadata to a JSON file
            output_metadata_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_objects.json")
            with open(output_metadata_path, "w") as json_file:
                json.dump(metadata, json_file, indent=4)

if __name__ == "__main__":
    # Define the folders
    clips_folder = "data/clips"
    output_folder = "data/metadata"

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Run the detection on all videos in the clips folder
    detect_objects_in_clips(clips_folder, output_folder)
