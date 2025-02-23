import json
import re
import os
from moviepy.editor import AudioFileClip

def calculate_sentence_durations(script_text, audio_duration):
    """Calculate how long each sentence should last based on word count."""
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    word_counts = [len(re.findall(r'\b\w+\b', sentence)) for sentence in sentences]
    total_words = sum(word_counts)

    # Calculate each sentence's duration proportionally to its word count
    sentence_durations = [(words / total_words) * audio_duration for words in word_counts]
    return sentences, sentence_durations

def match_script_to_clips(script_path, metadata_folder, audio_path, output_matches_path):
    """Match each sentence in the script to video clips with appropriate durations."""

    # Step 1: Get audio duration from the narration file
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return

    with AudioFileClip(audio_path) as narration_audio:
        audio_duration = narration_audio.duration

    print(f"Total narration audio duration: {audio_duration:.2f} seconds")

    # Step 2: Load the script and calculate sentence durations
    with open(script_path, "r") as file:
        script_text = file.read()

    sentences, sentence_durations = calculate_sentence_durations(script_text, audio_duration)
    print(f"Found {len(sentences)} sentences in the script.")

    # Step 3: Load metadata for all videos
    metadata = {}
    for metadata_file in os.listdir(metadata_folder):
        if metadata_file.endswith("_objects.json"):
            video_name = metadata_file.replace("_objects.json", ".mp4")
            with open(os.path.join(metadata_folder, metadata_file), "r") as file:
                metadata[video_name] = json.load(file)

    if not metadata:
        print("No metadata available.")
        return

    print(f"Available videos: {list(metadata.keys())}")

    # Step 4: Match each sentence to a different video
    matched_clips = []
    used_videos = set()
    available_videos = list(metadata.keys())

    for sentence, duration in zip(sentences, sentence_durations):
        key_phrases = re.findall(r'\b\w+\b', sentence.lower())
        best_match = None
        highest_score = 0

        # Step 4a: Check available videos (reset if all are used)
        if len(used_videos) == len(available_videos):
            print("All videos have been used. Resetting available videos.")
            used_videos.clear()

        # Step 4b: Find the best matching video that hasn't been used yet
        for video_name in available_videos:
            if video_name in used_videos:
                continue  # Skip already-used videos

            for entry in metadata[video_name]:
                detected_objects = [obj.lower() for obj in entry["objects"]]
                score = sum(1 for phrase in key_phrases if phrase in detected_objects)

                if score > highest_score:
                    highest_score = score
                    best_match = (video_name, entry["timestamp"])

        # Step 4c: If no match is found, default to the first unused video
        if not best_match:
            for video_name in available_videos:
                if video_name not in used_videos:
                    best_match = (video_name, metadata[video_name][0]["timestamp"])
                    break

        # Step 5: Add the match and mark the video as used
        if best_match:
            matched_clips.append({
                "sentence": sentence,
                "video": best_match[0],
                "timestamp": best_match[1],
                "duration": duration
            })
            used_videos.add(best_match[0])
            print(f"Matched sentence: '{sentence}' to video: '{best_match[0]}' at timestamp: {best_match[1]} for {duration:.2f} seconds")
        else:
            print(f"No match found for sentence: '{sentence}'")

    # Step 6: Save the matches to a JSON file
    if matched_clips:
        with open(output_matches_path, "w") as file:
            json.dump(matched_clips, file, indent=4)
        print(f"Matched clips saved to {output_matches_path}")
    else:
        print("No clips were matched to any sentence.")

    return matched_clips

# Example usage
output_matches_path = "data/matches/matched_clips.json"
match_script_to_clips(
    script_path="data/script/narration_script.txt",
    metadata_folder="data/metadata/",
    audio_path="data/audio/narration_audio.mp3",
    output_matches_path=output_matches_path
)
