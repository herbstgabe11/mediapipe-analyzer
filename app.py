import os
import json
import cv2
import requests
from flask import Flask, request, jsonify, render_template_string

# Force MediaPipe to run on CPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["DISABLE_MEDIAPIPE_GPU"] = "true"

import mediapipe as mp

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

WEBHOOK_URL = "https://herbstgabe.app.n8n.cloud/webhook-test/5263ccbb-5c4c-4199-9b9c-a7f0e3329b28"

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
        keypoints = extract_pose(filename)
        os.remove(filename)

        # Send to webhook
        res = requests.post(WEBHOOK_URL, json={"keypoints": keypoints})
        return jsonify({"status": "success", "webhook_code": res.status_code}), 200

    except Exception as e:
        os.remove(filename)
        return f"Processing error: {str(e)}", 500

def extract_pose(video_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        smooth_landmarks=True
    )

    cap = cv2.VideoCapture(video_path)
    results = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = pose.process(image_rgb)

        if output.pose_landmarks:
            frame_data = []
            for lm in output.pose_landmarks.landmark:
                frame_data.append({
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility
                })
            results.append(frame_data)

    cap.release()
    return results

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
