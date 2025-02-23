import os
import cv2
import time
import numpy as np
from sklearn.cluster import KMeans
from pathlib import Path


class VideoMetadata:
    def __init__(self, width, duration):
        self.width = width
        self.duration = duration


class VideoParser:
    def __init__(self, video_path):
        self.video_path = video_path
        self.meta = None
        self.frames = []
        self.frame_diffs = []

    def parse_video(self):
        """
        Parse the video to extract frames and calculate frame differences.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Failed to open video: {self.video_path}")
            return []

        # Get video metadata
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
        self.meta = VideoMetadata(width, duration)

        nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames = []
        self.frame_diffs = []

        prev_frame = None
        for i in range(nframes):
            ret, frame = cap.read()
            if not ret:
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frames.append(gray_frame)

            if prev_frame is not None:
                # Calculate difference between the current and previous frame
                diff = cv2.absdiff(gray_frame, prev_frame)
                self.frame_diffs.append(np.sum(diff))  # Sum of pixel differences as a measure of 'difference'

            prev_frame = gray_frame

        cap.release()

        return self.frames

    def get_frame_features(self):
        """
        Return frame difference features.
        """
        return np.array(self.frame_diffs)


class Clock:
    @staticmethod
    def now():
        return time.time()

    @staticmethod
    def elapsed(t0):
        return time.time() - t0


# Video processing and thumbnail detection function
def run_hecate(video_path, output_dir="output", n_thumbnails=5, debug=False):
    """
    Main function to process the video:
    1. Parse the video
    2. Detect keyframes
    3. Generate and save thumbnails
    """
    if not Path(video_path).exists():
        print(f"File does not exist: {video_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    t0 = Clock.now()
    parser = VideoParser(video_path)

    # Parse video and get frames
    frames = parser.parse_video()
    if not frames:
        print("Failed to parse the video")
        return

    # Extract frame features (using frame differences here)
    diff_features = parser.get_frame_features()

    # Thumbnail detection using k-means clustering
    thumbnail_indices = detect_thumbnail_frames(video_path, n_thumbnails, frames, diff_features, debug)

    # Generate thumbnails if required
    generate_thumbnails(video_path, debug, output_dir, thumbnail_indices)

    if debug:
        print(f"Elapsed time: {Clock.elapsed(t0)} seconds")


# Thumbnail detection using k-means clustering
def detect_thumbnail_frames(video_path, n_thumbnails=5, frames=None, diff_features=None, debug=False):
    """
    Detects keyframes using k-means clustering to select representative thumbnails.
    """
    nframes = len(frames)
    valid_frames = frames
    frame_diffs = diff_features

    # Apply k-means clustering on the frame differences to find shot boundaries
    kmeans = KMeans(n_clusters=min(30, max(5, n_thumbnails)), random_state=0).fit(np.array(valid_frames).reshape(nframes, -1))

    # Get the cluster centers (representative frames)
    labels = kmeans.labels_

    # Calculate cluster sizes and sort by size
    cluster_sizes = [np.sum(labels == i) for i in range(len(kmeans.cluster_centers_))]
    sorted_clusters = np.argsort(cluster_sizes)[::-1]  # Sort clusters by size, descending

    thumbnail_indices = []
    for cluster in sorted_clusters:
        # Find the frame with minimum difference in the cluster
        cluster_indices = np.where(labels == cluster)[0]

        # Ensure that the index is within the bounds of the frame_diffs array
        # We're selecting the best frame based on the smallest frame difference
        valid_cluster_indices = [idx for idx in cluster_indices if idx < len(frame_diffs)]

        if valid_cluster_indices:  # Check if there are valid indices to select from
            best_frame_idx = min(valid_cluster_indices, key=lambda idx: frame_diffs[idx])
            thumbnail_indices.append(best_frame_idx)

    # Return an empty list if no thumbnails are selected
    return thumbnail_indices if thumbnail_indices else []




def generate_thumbnails(video_path, debug, output_dir, thumbnail_indices):
    if thumbnail_indices is None:
        print("No thumbnails found.")
        return  # Exit the function if no thumbnails are found

    # Process frames and save the selected thumbnails
    video_capture = cv2.VideoCapture(video_path)
    frame_idx = 0
    njpg_cnt = 0
    filename = os.path.basename(video_path)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Check if the current frame is in the selected thumbnail list
        if frame_idx in thumbnail_indices:
            # Here you can save the thumbnail or process it as needed
            output_path = os.path.join(output_dir, f"{filename}_thumb_{njpg_cnt}.jpg")
            cv2.imwrite(output_path, frame)
            njpg_cnt += 1

        frame_idx += 1

    video_capture.release()



# Example of using the above functions
video_path = 'pearl.mp4'
run_hecate(video_path, output_dir="output/pearl", n_thumbnails=5, debug=True)
