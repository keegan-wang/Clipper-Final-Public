import boto3
import os
import time
import cv2
import numpy as np
from collections import defaultdict
import re


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
        job_id = response.get('JobId', '')
        print(f"Raw JobId from start_label_detection: {job_id}")  # Add this line
        if not is_valid_job_id(job_id):
            print(f"Invalid JobId: {job_id}")
            return None
        print(f"Job started with ID: {job_id}")
        return job_id
    except Exception as e:
        print(f"Error starting video analysis: {e}")
        exit()

# Validate length and format of JobId
def is_valid_job_id(job_id):
    if len(job_id) > 64:
        print(f"Invalid JobId length: {len(job_id)} (max 64 characters allowed).")
        return False
    if re.match(r'^[a-zA-Z0-9-_]{1,64}$', job_id):
        print(f"Valid JobId: {job_id}")
        return True
    else:
        print(f"Invalid JobId format: {job_id}")
        return False


# Track label frequencies over time
def track_label_frequencies(job_id):
    label_frequencies = defaultdict(list)
    try:
        while True:
            result = rekognition.get_label_detection(JobId=job_id)
            status = result['JobStatus']
            if status == 'SUCCEEDED':
                print("Video analysis succeeded.")
                for label in result['Labels']:
                    timestamp = label['Timestamp']
                    label_name = label['Label']['Name']
                    label_frequencies[timestamp].append(label_name)
                return label_frequencies
            elif status == 'FAILED':
                print("Video analysis failed.")
                return None

            print("Waiting for the job to complete...")
            time.sleep(5)  # Wait for 5 seconds before polling again
    except Exception as e:
        print(f"Error retrieving video analysis results: {e}")
        exit()



# Extract sub-video from the original video based on start and end time using OpenCV
def extract_sub_video(input_video, start_time, end_time, output_video):
    try:
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            print(f"Error opening video file {input_video}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Video Width: {frame_width}, Height: {frame_height}, FPS: {fps}, Total Frames: {total_frames}")

        duration = total_frames / fps
        print(f"Extracting from {start_time:.2f}s to {end_time:.2f}s. Video duration: {duration:.2f}s")

        if end_time > duration:
            end_time = duration

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))

        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        end_time_ms = end_time * 1000
        while cap.isOpened():
            ret, frame = cap.read()
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC)
            if not ret or current_time > end_time_ms:
                break
            out.write(frame)

        cap.release()
        out.release()
        print(f"Extracted sub-video from {start_time} to {end_time}")
    except Exception as e:
        print(f"Error extracting sub-video: {e}")


# Suggest sub-video division points based on dynamically determined threshold
def suggest_subvideo_divisions_dynamic_threshold(label_frequencies):
    frequency_changes = []
    last_labels = None
    for timestamp, labels in sorted(label_frequencies.items()):
        current_labels = set(labels)
        if last_labels is not None:
            change = len(current_labels.symmetric_difference(last_labels)) / len(current_labels.union(last_labels))
            frequency_changes.append(change)
        last_labels = current_labels

    frequency_changes = np.array(frequency_changes)
    mean_change = np.mean(frequency_changes)
    std_dev_change = np.std(frequency_changes)
    thresh = 1.8
    dynamic_threshold = mean_change + thresh * std_dev_change

    print(f"Dynamic threshold based on mean and standard deviation: {dynamic_threshold:.4f}")

    last_labels = None
    divisions = []
    start_time = 0

    for timestamp, labels in sorted(label_frequencies.items()):
        current_labels = set(labels)
        if last_labels is not None:
            change = len(current_labels.symmetric_difference(last_labels)) / len(current_labels.union(last_labels))
            if change > dynamic_threshold:
                end_time = timestamp / 1000
                divisions.append((start_time, end_time))
                start_time = end_time
        last_labels = current_labels

    end_time = max(label_frequencies.keys()) / 1000
    divisions.append((start_time, end_time))
    return divisions

# Main function
def main():
    download_video_from_s3()
    job_id = start_video_analysis()
    label_frequencies = track_label_frequencies(job_id)
    divisions = suggest_subvideo_divisions_dynamic_threshold(label_frequencies)
    print(f"Suggested sub-video divisions:")
    for i, (start, end) in enumerate(divisions):
        print(f"Sub-video {i+1}: Start = {start:.2f}s, End = {end:.2f}s")
        extract_sub_video(local_video_path, start, end, f"sub_video_{i}.mp4")

if __name__ == "__main__":
    main()
