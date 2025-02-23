from IPython.display import display, Image, Audio

import cv2  # We're using OpenCV to read video, to install !pip install opencv-python
import base64
import time
from openai import OpenAI
import openai
import os
import requests
import json
import asyncio
import time
import standardize

# client = OpenAI(api_key="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")
client = openai.AsyncOpenAI(api_key='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')


def generate_metadata(filepath, intermediate, output_file):
    video = filepath
    # video = "data/bison.mp4"
    userprompt = "prompts/userprompt.txt"
    systemprompt = "prompts/singlesystemprompt.txt"
    batch_size = 1
    start_time = time.time()

    video = cv2.VideoCapture(video)

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

    asyncio.run(process_batches(base64Frames, batch_size, intermediate,systemprompt))

    standardize.standardize_json(intermediate, output_file)

    print(f"Total time taken: {time.time() - start_time} seconds")

def reader(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    
def writer(data, file_path="output.json"):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print(f"✅ Output saved to {file_path}")


def api_call(frames, systemprompt):
    PROMPT_MESSAGES = [
            {
                "role": "system",
                "content": reader(systemprompt)
            },
            {
                "role": "user",
                "content": [
                    # reader(userprompt),
                    # {"image": image, "resize": 768},
                    *map(lambda x: {"image": x["image"], "resize": 768}, frames)
                ]
            }
        ]
    
    params = {
        "model": "gpt-4o",
        "messages": PROMPT_MESSAGES,
        "response_format": { "type": "json_object" }
    }
    result = client.chat.completions.create(
        **params
    )
    return result.choices[0].message.content


# try:
#     json_output = api_call(base64Frames)
#     print(json_output)
#     # Ensure the output is valid JSON
#     try:
#         json_data = json.loads(json_output)
#     except json.JSONDecodeError:
#         print("❌ GPT output is not valid JSON!")

#     writer(json_data, output_file)
# except Exception as e:
#     print(f"❌ API call failed: {e}")

async def send_request(batch, batch_index, batch_size, systemprompt):
    func_start = time.time()
    # print(f"start time {batch_index}: {func_start - start_time}")
    PROMPT_MESSAGES = [
        {"role": "system", "content": " Your batch size n is: " + str(batch_size)+ reader(systemprompt)},
        {"role": "user", "content": [*map(lambda x: {"image": x["image"], "resize": 768}, batch)]}
    ]

    params = {
        "model": "gpt-4o",  # Using GPT-4o-mini for faster response
        "messages": PROMPT_MESSAGES,
        "response_format": { "type": "json_object" }
    }
    result = await client.chat.completions.create(
        **params
    )
    # print(f"end time {batch_index}: {time.time() - func_start}")

    # return result.choices[0].message.content
    try:
        parsed_json = json.loads(result.choices[0].message.content)
    except json.JSONDecodeError:
        print(f"❌ Failed to parse JSON for batch {batch_index}")
        return {}

    # ✅ Update timestamps to match actual video time
    updated_json = {}
    for (key, value) in parsed_json.items():
        new_timestamp = str(int(key) + batch_index)
        updated_json[new_timestamp] = value  # Assign correct timestamp

    return updated_json  # ✅ Now returns correctly labeled timestamps

async def process_batches(base64Frames, batch_size, output_file,systemprompt):
    batches = [base64Frames[i:min(i + batch_size, len(base64Frames))] for i in range(0, len(base64Frames), batch_size)]

    tasks = [send_request(batch, i, batch_size, systemprompt) for i, batch in enumerate(batches)]
    results = await asyncio.gather(*tasks)

    # Remove None responses (failed calls)
    results = [res for res in results if res is not None]

    # Merge all batch results into one JSON
    # for i, result in enumerate(results):
    #     try:
    #         # print(result)
    #         # print()
    #         results[i] = json.loads(result)
    #     except json.JSONDecodeError:
    #         print("❌ GPT output is not valid JSON!")

    # print(results)
    final_output = {}
    for batch_result in results:
        final_output.update(batch_result)

    # Write final output to file
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(final_output, file, indent=4)
    print(f"✅ Output saved to {output_file}")

# Run async function
generate_metadata("data/bigbigfish.mp4", "output/output.json", "output/output_standardized.json")
