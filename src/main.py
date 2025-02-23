import subprocess
import os

def main():
    # Define paths
    script_path = "data/script/narration_script.txt"
    audio_path = "data/audio/narration_audio.mp3"
    metadata_folder = "data/metadata"
    matches_path = "data/matches/matched_clips.json"
    output_path = "outputs/final_video.mp4"
    clips_folder = "data/clips"

    # Ensure all uploaded videos are listed
    uploaded_videos = [os.path.join(clips_folder, f) for f in os.listdir(clips_folder) if f.endswith((".mp4", ".mov"))]

    if not uploaded_videos:
        print("No videos found in the clips folder. Exiting.")
        return

    print("Videos to be analyzed:", uploaded_videos)

    try:
        # Step 1: Generate AI narration
        print("Generating AI narration...")
        subprocess.run(["python3", "src/scriptToTTS.py"], check=True)

        # Step 2: Detect objects in videos
        #print("Running scene detection...")
        #subprocess.run(["python3", "src/sceneDetection.py"], check=True)

        # Step 3: Match script to clips and save matches
        print("Matching script to clips...")
        subprocess.run(["python3", "src/scriptMatching.py"], check=True)

        # Step 4: Edit and export the final video using matches
        print("Starting video editing...")
        subprocess.run(
            ["python3", "src/videoProcessing.py", script_path, audio_path, matches_path, output_path],
            check=True
        )

        print("Video processing completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"Error during video processing: {e}")

if __name__ == "__main__":
    main()