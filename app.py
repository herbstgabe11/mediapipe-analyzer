import os
import tempfile
import json
import requests
from flask import Flask, request, jsonify, render_template_string
import mediapipe as mp
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Your test webhook
WEBHOOK_URL = "https://herbstgabe.app.n8n.cloud/webhook-test/5263ccbb-5c4c-4199-9b9c-a7f0e3329b28"

# Upload form
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
def upload_video():
    video = request.files['video']
    if not video:
        return "No file uploaded", 400

    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(filepath)

    # Analyze pose
    pose_data = analyze_pose(filepath)
    os.remove(filepath)

    # Send to GPT webhook
    try:
        res = requests.post(WEBHOOK_URL, json={"keypoints": pose_data})
        return f"Video processed. Webhook response: {res.status_code}", 200
    except Exception as e:
        return f"Error sending to webhook: {e}", 500

def analyze_pose(video_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        smooth_landmarks=True
    )
    cap = cv2.VideoCapture(video_path)
    keypoints = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.pose_landmarks:
            frame_keypoints = [
                {
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility
                }
                for lm in results.pose_landmarks.landmark
            ]
            keypoints.append(frame_keypoints)

    cap.release()
    return keypoints
