import json
from collections import defaultdict
from openai import OpenAI

def standardize_json(input_json, output_json):

    client = OpenAI(api_key="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")

    output_file = "output/standardized.json"

    def reader(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()


    # Load the JSON file
    with open(input_json, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    # Create a dictionary to store object counts
    objects = {}

    # Iterate through all timestamps
    for timestamp, data in json_data.items():
        if "objects" in data:
            for obj in data["objects"]:
                objects[obj] = ""

    # Save extracted objects to a file for debugging
    print(f"✅ Extracted {len(objects)} unique objects.")

    def api_call(dic):
        PROMPT_MESSAGES = [
                {
                    "role": "system",
                    "content": reader('prompts/standardizeprompt.txt')
                },
                {
                    "role": "user",
                    "content": f"{dic}"
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
    try:
        parsed_json = json.loads(api_call(objects))
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON")


    # with open(output_file, "w", encoding="utf-8") as file:
    #     json.dump(parsed_json, file, indent=4)
    # print(f"✅ Output saved to {output_file}")


    for timestamp, data in json_data.items():
        if "objects" in data:
            categorized_list = [parsed_json.get(obj, "Unknown") for obj in data["objects"]]
            json_data[timestamp]["categories"] = list(set(categorized_list))  # Remove duplicates

    # ✅ Save updated JSON file
    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4)

    print("✅ Updated JSON saved as data_categorized.json")
