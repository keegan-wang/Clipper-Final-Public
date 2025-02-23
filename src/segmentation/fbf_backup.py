import boto3
import time
import cv2
from collections import defaultdict

# Initialize Rekognition client and S3 client
rekognition = boto3.client('rekognition')
s3_client = boto3.client('s3')

# Video details
bucket_name = 'clipperth25'
video_file_name = 'jelly.mov'
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

# Divide video into segments based on label frequency changes
def segment_video_based_on_frequencies(label_frequencies, input_video):
    # Define a threshold for frequency change detection (you can adjust this value)
    threshold = 0.2  # Adjust as needed to determine significant changes
    last_labels = None
    segments = []
    start_time = 0

    # Analyze label frequencies to detect where to split the video
    for timestamp, labels in sorted(label_frequencies.items()):
        # Convert list of labels to a set for unique labels
        current_labels = set(labels)
        
        # Calculate frequency change (if significant, consider this a segment boundary)
        if last_labels is not None:
            change = len(current_labels.symmetric_difference(last_labels)) / len(current_labels.union(last_labels))
            if change > threshold:  # Significant change in label frequencies
                end_time = timestamp / 1000  # Convert ms to seconds
                # Create the sub-video from start_time to end_time
                segment_output = f"sub_video_{len(segments)}.mp4"
                extract_sub_video(input_video, start_time, end_time, segment_output)
                segments.append((start_time, end_time))
                start_time = end_time

        last_labels = current_labels

    # Extract the final segment
    end_time = max(label_frequencies.keys()) / 1000  # Use the last timestamp
    segment_output = f"sub_video_{len(segments)}.mp4"
    extract_sub_video(input_video, start_time, end_time, segment_output)
    segments.append((start_time, end_time))

    return segments

# Main function
def main():
    # Step 1: Download video from S3
    download_video_from_s3()

    # Step 2: Start Rekognition video analysis
    job_id = start_video_analysis()

    # Step 3: Track label frequencies
    label_frequencies = track_label_frequencies(job_id)

    # Step 4: Segment video based on label frequencies
    segments = segment_video_based_on_frequencies(label_frequencies, local_video_path)

    print(f"Created {len(segments)} sub-video(s)")

if __name__ == "__main__":
    main()
