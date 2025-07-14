
import os
import json
import cv2
import replicate
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_HTML = '''
<!doctype html>
<title>Upload a Swing Video (.mp4)</title>
<h1>Upload a Swing Video (.mp4)</h1>
<form method=post enctype=multipart/form-data action="/upload">
  <input type=file name=video>
  <input type=submit value=Upload>
</form>
'''

@app.route('/')
def index():
    return render_template_string(UPLOAD_HTML)

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return "No video file provided", 400

    file = request.files['video']
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    # Check duration
    cap = cv2.VideoCapture(filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frames / fps if fps > 0 else 0
    cap.release()

    if duration > 4:
        os.remove(filename)
        return "Video too long. Must be 4 seconds or less.", 400

    try:
        # Use your latest working API key
        replicate.api_token = "r8_QlJx73rI6oq5p4pD37ngjFQEIrxcYIY37ZSTJ"

        output = replicate.run(
            "vegetebird/human-pose-estimation:latest",
            input={"video": open(filename, "rb")}
        )

        os.remove(filename)
        return jsonify({"status": "success", "keypoints": output}), 200

    except Exception as e:
        os.remove(filename)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
