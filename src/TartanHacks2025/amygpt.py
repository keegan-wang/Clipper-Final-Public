from IPython.display import display, Image, Audio

import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import os
import requests
import json

client = OpenAI(api_key="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")
video = cv2.VideoCapture("data/bison.mp4")

base64Frames = []

fps = int(video.get(cv2.CAP_PROP_FPS))  # Frames per second
total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))  # Total frames
duration = total_frames // fps  # Video duration in seconds
frame_frequency = fps

print(f"Video FPS: {fps}, Total Frames: {total_frames}, Duration: {duration} seconds")

second = 0
frame_count = 0
while video.isOpened():
    success, frame = video.read()
    if not success:
        break

    if frame_count % frame_frequency == 0:
        _, buffer = cv2.imencode(".jpg", frame)
        base64_frame = base64.b64encode(buffer).decode("utf-8")
        base64Frames.append({"image": base64_frame, "resize": 768, "timestamp": second})
        # base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        # base64Frames[second] = base64.b64encode(buffer).decode("utf-8")
        second += 1

    frame_count += 1


video.release()

print(len(base64Frames), "frames read.")

#def api_call(image):
    # PROMPT_MESSAGES = [
    #         {
    #             "role": "user",
    #             "content": [
    #                 "Analyze this frame and identify all objects you see. Return the output as a JSON list of detected objects.",
    #                 # {"image": image, "resize": 768},
    #                 *map(lambda x: {"image": image, "resize": 768}, base64Frames[0::1])
    #             ],
    #         }
    #     ]
    
    # print(PROMPT_MESSAGES)
    
   # PROMPT_MESSAGES = [
      #  {
          #  "role": "user",
          #  "content": [
          #      "Analyze these frames and identify all objects in each. Return the output as a JSON dictionary with timestamps as keys and detected objects as values.",
          #      *base64Frames,  # Unpack all images in the message
          #  ],
      #  }
 #   ]
 #   print(PROMPT_MESSAGES)

  #  params = {
#        "model": "gpt-4o",
#        "messages": PROMPT_MESSAGES,
#        "max_tokens": 200,
#    }
    # try:
    #     result = client.chat.completions.create(**params)
    #     identified_objects = json.loads(result.choices[0].message.content)  # Parse JSON response

    #     # Store identified objects in dictionary with timestamp as key
    #     frame_data[second] = identified_objects

    #     print(f"Processed second {second}: {identified_objects}")

    # except Exception as e:
    #     print(f"Error at second {second}: {str(e)}")
    #     frame_data[second] = {"error": str(e)}

#    try:
 #       result = client.chat.completions.create(**params)
 #       identified_objects = json.loads(result.choices[0].message.content)  # Parse JSON response
 #       frame_data[second] = identified_objects
#        print(f"Processed second {second}: {identified_objects}")
 #   except Exception as e:
 #       print(f"Error at second {second}: {str(e)}")
 #       frame_data[second] = {"error": str(e)}

#for frame in base64Frames:
#    api_call(frame)


def api_call():
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": "Analyze these frames and identify all objects in each. Return the output as a JSON dictionary with timestamps as keys and detected objects as values."
        }
    ]

    # Add each frame as a separate message
    for frame in base64Frames:
        PROMPT_MESSAGES.append({
            "role": "user",
            # "content": {"image": frame["image"], "resize": frame["resize"], "timestamp": frame["timestamp"]}
            "content": {"image": "asss", "resize": frame["resize"], "timestamp": frame["timestamp"]}
        })

    print(PROMPT_MESSAGES)

    params = {
        "model": "gpt-4-turbo",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 200,
    }

    try:
        result = client.chat.completions.create(**params)
        print(result)
        print(result.choices[0].message.content)
    except Exception as e:
        print(f"Error during API call: {str(e)}")


api_call()
# for frame in base64Frames:
#     api_call(frame)

# display_handle = display(None, display_id=True)
# for img in base64Frames:
#     display_handle.update(Image(data=base64.b64decode(img.encode("utf-8"))))
#     time.sleep(0.025)



# PROMPT_MESSAGES = [
#     {
#         "role": "user",
#         "content": [
#             "These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
#             *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::50]),
#         ],
#     },
# ]
# params = {
#     "model": "gpt-4o",
#     "messages": PROMPT_MESSAGES,
#     "max_tokens": 200,
# }

# result = client.chat.completions.create(**params)
# print(result.choices[0].message.content)