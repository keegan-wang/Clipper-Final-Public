from IPython.display import display, Image, Audio

import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import os
import requests

def reader(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    
script = "script.txt"

result = reader(script)

response = requests.post(
    "https://api.openai.com/v1/audio/speech",
    headers={
        "Authorization": "Bearer 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",
    },
    json={
        "model": "tts-1-1106",
        "input": result,
        "voice": "onyx",
    },
)

audio = b""
for chunk in response.iter_content(chunk_size=1024 * 1024):
    audio += chunk

audio_filename = "audio/output_audio.mp3"

# Save the audio data to a file
with open(audio_filename, "wb") as audio_file:
    audio_file.write(audio)

print(f"Audio saved as {audio_filename}")