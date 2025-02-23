import os
import json
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, afx
from nltk.tokenize import sent_tokenize
import random

def load_metadata(metadata_folder):
    """Load metadata for uploaded videos."""
    metadata = {}
    for file in os.listdir(metadata_folder):
        if file.endswith("_objects.json"):
            video_name = file.replace("_objects.json", ".mp4")
            with open(os.path.join(metadata_folder, file), "r") as f:
                metadata[video_name] = json.load(f)
    return metadata


def edit_video_with_matches(matches_path, audio_path, clips_folder, output_path):
    """Create a video using the matched clips with synchronized audio."""

    # Step 1: Load matched clips
    if not os.path.exists(matches_path):
        print(f"Error: Matches file not found at {matches_path}")
        return

    with open(matches_path, "r") as file:
        matched_clips = json.load(file)

    if not matched_clips:
        print("No matched clips available.")
        return

    print(f"Loaded {len(matched_clips)} matched clips.")

    # Step 2: Load narration audio
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return

    narration_audio = AudioFileClip(audio_path)
    total_narration_duration = narration_audio.duration
    sentence_duration = total_narration_duration / len(matched_clips)

    print(f"Narration duration: {narration_audio.duration} seconds.")
    print(f"Each sentence will have a duration of {sentence_duration} seconds.")

    # Step 3: Create video clips from matches
    video_clips = []
    for index, match in enumerate(matched_clips):
        video_file = os.path.join(clips_folder, match["video"])
        timestamp = match["timestamp"]

        if not os.path.exists(video_file):
            print(f"Video file not found: {video_file}. Skipping.")
            continue

        print(f"Using video '{video_file}' for sentence: '{match['sentence']}'")
        try:
            clip = VideoFileClip(video_file).subclip(timestamp, timestamp + sentence_duration)
            video_clips.append(clip)
        except Exception as e:
            print(f"Error processing clip '{video_file}': {e}")
            continue

    if not video_clips:
        print("No video clips were created. Aborting.")
        return

    # Step 4: Concatenate video clips
    print("Concatenating video clips...")
    final_video = concatenate_videoclips(video_clips)

    # Step 5: Sync the narration audio with the video
    if narration_audio.duration > final_video.duration:
        print("Trimming audio to match video duration.")
        narration_audio = narration_audio.subclip(0, final_video.duration)

    final_video = final_video.set_audio(narration_audio)

    # Step 6: Export the final video
    print(f"Exporting video to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    if os.path.exists(output_path):
        print(f"Video saved successfully to {output_path}")
    else:
        print("Error: Video file was not created.")

# Example usage
edit_video_with_matches(
    "data/matches/matched_clips.json",
    "data/audio/narration_audio.mp3",
    "data/clips",
    "outputs/final_video.mp4"
)
