import os
import replicate
import tempfile
import cv2
from flask import Flask, request, jsonify, render_template_string

# Initialize app
app = Flask(__name__)

UPLOAD_HTML = '''
<!doctype html>
<title>Upload a Swing Video</title>
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
    if file.filename == '':
        return "No selected file", 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        file.save(tmp.name)
        video_path = tmp.name

    # Check duration (must be ≤ 4 sec)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps else 0
    cap.release()

    if duration > 4:
        os.remove(video_path)
        return "Video too long. Must be 4 seconds or less.", 400

    try:
        os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

        output = replicate.run(
            "vegetebird/human-pose-estimation:latest",
            input={"video": open(video_path, "rb")}
        )

        os.remove(video_path)
        return jsonify({"status": "success", "keypoints": output}), 200

    except Exception as e:
        os.remove(video_path)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
