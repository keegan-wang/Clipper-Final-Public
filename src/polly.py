from dotenv import load_dotenv
import os
import boto3

# Load environment variables from .env
load_dotenv()

# Access the variables
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

# Initialize Amazon Polly client
polly_client = boto3.client(
    "polly",
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

# Test Polly
response = polly_client.synthesize_speech(
    Text="Hello, this is Amazon Polly!",
    OutputFormat="mp3",
    VoiceId="Joanna"
)

# Save the audio file
with open("output2.mp3", "wb") as file:
    file.write(response["AudioStream"].read())

print("Audio file saved as output.mp3")
