import boto3
import os
import time
import cv2
import numpy as np
from collections import defaultdict

# Initialize Rekognition client and S3 client
rekognition = boto3.client(
    'rekognition',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
s3_client = boto3.client(
    's3',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


# Video details
bucket_name = 'clipperth25'
video_file_name = 'jellypeng.mp4'
local_video_path = 'local_video.mp4'  # Local path to save the downloaded video

# Download video from S3 to local machine
def download_video_from_s3():
    try:
        print(f"Downloading {video_file_name} from S3 to {local_video_path}")
        s3_client.download_file(bucket_name, video_file_name, local_video_path)
        print(f"Downloaded {video_file_name} successfully.")
    except Exception as e:
        print(f"Error downloading the video: {e}")
        exit()

# Start video label detection with Rekognition
def start_video_analysis():
    try:
        print("Starting video label detection with Rekognition...")
        response = rekognition.start_label_detection(
            Video={'S3Object': {'Bucket': bucket_name, 'Name': video_file_name}}
        )
        job_id = response['JobId']
        print(f"Job started with ID: {job_id}")
        return job_id
    except Exception as e:
        print(f"Error starting video analysis: {e}")
        exit()

# Track label frequencies over time
def track_label_frequencies(job_id):
    label_frequencies = defaultdict(list)  # A dictionary to store the frequency of labels per timestamp

    try:
        while True:
            result = rekognition.get_label_detection(JobId=job_id)
            status = result['JobStatus']
            if status == 'SUCCEEDED':
                print("Video analysis succeeded.")
                # Track frequencies of labels over time
                for label in result['Labels']:
                    timestamp = label['Timestamp']
                    label_name = label['Label']['Name']
                    label_frequencies[timestamp].append(label_name)
                return label_frequencies
            elif status == 'FAILED':
                print("Video analysis failed.")
                return None
            print("Waiting for the job to complete...")
            time.sleep(5)
    except Exception as e:
        print(f"Error retrieving video analysis results: {e}")
        exit()

# Extract sub-video from the original video based on start and end time using OpenCV
def extract_sub_video(input_video, start_time, end_time, output_video):
    try:
        # Open the input video using OpenCV
        cap = cv2.VideoCapture(input_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Create VideoWriter to save the output sub-video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4 format
        out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))

        # Start reading from the video and write frames to the output video
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_time * fps)  # Set starting point
        end_frame = end_time * fps
        while cap.isOpened():
            ret, frame = cap.read()
            current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)

            if not ret or current_frame > end_frame:
                break
            out.write(frame)  # Write the current frame to the sub-video

        cap.release()
        out.release()
        print(f"Extracted sub-video from {start_time} to {end_time}")
    except Exception as e:
        print(f"Error extracting sub-video: {e}")

# Suggest sub-video division points based on dynamically determined threshold
def suggest_subvideo_divisions_dynamic_threshold(label_frequencies):
    # Calculate the frequency of label changes across timestamps
    frequency_changes = []

    last_labels = None
    for timestamp, labels in sorted(label_frequencies.items()):
        current_labels = set(labels)
        
        if last_labels is not None:
            # Calculate the symmetric difference between current and previous label sets
            change = len(current_labels.symmetric_difference(last_labels)) / len(current_labels.union(last_labels))
            frequency_changes.append(change)
        
        last_labels = current_labels

    # Convert frequency changes to a numpy array for statistical analysis
    frequency_changes = np.array(frequency_changes)

    # Calculate the mean and standard deviation of the frequency changes
    mean_change = np.mean(frequency_changes)
    std_dev_change = np.std(frequency_changes)

    # Define a dynamic threshold based on the mean and standard deviation
    thresh = 2
    dynamic_threshold = mean_change + thresh * std_dev_change  # Example: 2 standard deviations above the mean

    print(f"Dynamic threshold based on mean and standard deviation: {dynamic_threshold:.4f}")

    # Analyze label frequencies to detect where to suggest splits
    last_labels = None
    divisions = []
    start_time = 0

    for timestamp, labels in sorted(label_frequencies.items()):
        current_labels = set(labels)

        if last_labels is not None:
            change = len(current_labels.symmetric_difference(last_labels)) / len(current_labels.union(last_labels))

            if change > dynamic_threshold:  # Dynamic threshold for significant change
                end_time = timestamp / 1000  # Convert ms to seconds
                divisions.append((start_time, end_time))
                start_time = end_time

        last_labels = current_labels

    # Suggest the final division for the last segment
    end_time = max(label_frequencies.keys()) / 1000  # Use the last timestamp
    divisions.append((start_time, end_time))

    return divisions

# Main function
def main():
    # Step 1: Download video from S3
    download_video_from_s3()

    # Step 2: Start Rekognition video analysis
    job_id = start_video_analysis()

    # Step 3: Track label frequencies
    label_frequencies = track_label_frequencies(job_id)

    # Step 4: Suggest sub-video divisions based on dynamic threshold
    divisions = suggest_subvideo_divisions_dynamic_threshold(label_frequencies)

    # Step 5: Output the suggested sub-video divisions
    print(f"Suggested sub-video divisions:")
    for i, (start, end) in enumerate(divisions):
        print(f"Sub-video {i+1}: Start = {start:.2f}s, End = {end:.2f}s")

if __name__ == "__main__":
    main()
