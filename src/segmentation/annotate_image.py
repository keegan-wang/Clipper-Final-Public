import boto3
from PIL import Image, ImageDraw
import io
import os

# Initialize the S3 and Rekognition clients
# Initialize the S3 and Rekognition clients
rekognition = boto3.client(
    'rekognition',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
s3 = boto3.client(
    's3',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

# Specify the S3 bucket name and image file (object) name
bucket_name = 'clipperth25'  # Replace with your S3 bucket name
s3_object_name = 'penguin.png'  # Replace with the file name in your S3 bucket

# Download the image from the S3 bucket into memory
image_object = s3.get_object(Bucket=bucket_name, Key=s3_object_name)
image_data = image_object['Body'].read()  # Read the image data into memory

# Call Amazon Rekognition to detect objects in the image
response = rekognition.detect_labels(
    Image={'Bytes': image_data},  # Provide the image data as bytes
    MaxLabels=10,                 # Limit the number of labels returned (e.g., 10 labels)
    MinConfidence=75              # Set a minimum confidence threshold for detection (optional)
)

# Open the image with Pillow
image = Image.open(io.BytesIO(image_data))
draw = ImageDraw.Draw(image)

# Annotate the image with bounding boxes and labels
for label in response['Labels']:
    for instance in label['Instances']:
        if 'BoundingBox' in instance:
            box = instance['BoundingBox']
            width, height = image.size
            left = width * box['Left']
            top = height * box['Top']
            right = left + (width * box['Width'])
            bottom = top + (height * box['Height'])
            
            # Draw the bounding box
            draw.rectangle([left, top, right, bottom], outline='red', width=5)
            
            # Draw the label text
            draw.text((left, top), label['Name'], fill='red')
            
# Convert RGBA to RGB before saving
if image.mode in ("RGBA", "P"):  # Some PNGs might be in "P" mode
    image = image.convert("RGB")

# Save the image in a compatible format
# Print image mode before saving
print(f"Image mode before saving: {image.mode}")

# Ensure image is converted to RGB
if image.mode not in ("RGB", "L"):  # L mode is grayscale, RGB is normal color
    image = image.convert("RGB")
    print("Converted image to RGB mode")

# Save the image
annotated_image_path = "annotated_image.png"
image.save(annotated_image_path, format="PNG")  # Explicit format

image.show()  # Display image
print(f"Annotated image saved as '{annotated_image_path}'")

