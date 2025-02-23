from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import os
import random
import json


def edit_video(matched_clips, audio_path, input_folder, output_path):
    video_clips = []

    # If no matched clips, use fallback logic
    if not matched_clips:
        print("No exact or partial matches found. Falling back to default clip.")
        # Fallback: Choose the first clip in the input folder
        video_files = [f for f in os.listdir(input_folder) if f.endswith(".mp4")]
        if video_files:
            video_path = os.path.join(input_folder, video_files[0])
            video_clips.append(VideoFileClip(video_path).subclip(0, 5))  # Use the first 5 seconds

    else:
        # Load and cut each matched clip
        for clip_name, timestamp in matched_clips:
            video_path = os.path.join(input_folder, clip_name.replace("_objects.json", ".mp4"))
            clip = VideoFileClip(video_path).subclip(timestamp, timestamp + 5)
            video_clips.append(clip)

    if video_clips:
        # Concatenate all matched clips
        final_video = concatenate_videoclips(video_clips)

        # Load the narration audio
        narration_audio = AudioFileClip(audio_path)

        # Ensure the audio matches the video duration
        final_audio = narration_audio.set_duration(final_video.duration)

        # Set the final video's audio to the narration
        final_video = final_video.set_audio(final_audio)

        # Export the final video with audio
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    else:
        print("No video clips available to create final output.")

# Example usage
edit_video([], "data/audio/narration_audio.mp3", "data/clips", "outputs/final_video.mp4")
