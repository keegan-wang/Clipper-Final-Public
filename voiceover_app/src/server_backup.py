from flask import Flask, render_template, request, jsonify
import boto3
import os

app = Flask(__name__)

# Initialize the Amazon Polly client
polly = boto3.client('polly')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', 'Joanna')  # Default voice is Joanna if none is selected

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    try:
        # Use Amazon Polly to synthesize the speech
        response = polly.synthesize_speech(
            Text=text,
            VoiceId=voice,
            OutputFormat='mp3',
            Engine='standard'
        )

        # Save the audio stream to an MP3 file
        output_path = os.path.join('static', 'output.mp3')
        with open(output_path, 'wb') as file:
            file.write(response['AudioStream'].read())

        # Return the file URL to the frontend
        file_url = os.path.join('static', 'output.mp3')
        return jsonify({'file_url': file_url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
