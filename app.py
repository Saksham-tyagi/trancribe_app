# env\Scripts\activate 
import os
import whisper
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Load Whisper model (base, small, medium etc.)
model = whisper.load_model("small.en")

# Define directories for audio and transcripts
AUDIO_FOLDER = os.path.join("uploads", "audio")
TRANSCRIPT_FOLDER = os.path.join("uploads", "transcripts")
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream-chunk", methods=["POST"])
def stream_chunk():
    file = request.files.get("file")
    filename = request.form.get("filename")
    if not file or not filename:
        return jsonify({"error": "File or filename missing"}), 400

    # Save the audio chunk
    audio_path = os.path.join(AUDIO_FOLDER, file.filename)
    file.save(audio_path)

    # Define the transcript file path
    transcript_path = os.path.join(TRANSCRIPT_FOLDER, filename)

    # Check if the transcript file exists; if not, create it
    if not os.path.exists(transcript_path):
        print(f"Creating new transcript file: {transcript_path}")
        open(transcript_path, "w").close()  # Create an empty file

    # Transcribe the audio chunk using Whisper
    result = model.transcribe(audio_path)
    transcript = result.get("text", "").strip()

    # Append the transcript to the transcript file
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write(transcript + "\n")

    # # Optionally, you can remove the audio chunk after transcription
    # try:
    #     os.remove(audio_path)
    # except Exception as e:
    #     print(f"Error removing audio file {audio_path}: {e}")

    return jsonify({"transcript": transcript})

@app.route("/check-file", methods=["POST"])
def check_file():
    data = request.get_json()
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Filename not provided"}), 400

    transcript_path = os.path.join(TRANSCRIPT_FOLDER, filename)
    exists = os.path.exists(transcript_path)
    print(f"Checking existence of file: {filename}")
    print(f"Path: {transcript_path}")
    print(f"File exists: {exists}")
    return jsonify({"exists": exists})

@app.route("/reset-conversation", methods=["POST"])
def reset_conversation():
    return jsonify({"status": "Conversation reset"})

@app.route("/remove_all_files_in_folder", methods=["POST"])
def remove_all_files_in_folder():
    folder_path = AUDIO_FOLDER
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
        return jsonify({"status": "All files have been removed from the folder."})
    else:
        return jsonify({"status": "Folder does not exist or is not a directory."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
