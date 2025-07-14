import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string
import mediapipe as mp
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ n8n webhook URL
WEBHOOK_URL = "https://herbstgabe.app.n8n.cloud/webhook-test/5263ccbb-5c4c-4199-9b9c-a7f0e3329b28"

# Simple HTML form for testing in browser
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
    video = request.files.get('video')
    if not video:
        return "No video file found", 400

    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(filepath)

    try:
        keypoints = analyze_pose(filepath)
        os.remove(filepath)
        response = requests.post(WEBHOOK_URL, json={"keypoints": keypoints})
        return jsonify({"status": "sent", "response_code": response.status_code}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def analyze_pose(video_path):
    mp_pose = mp.solutions.pose
    # 👇 DISABLE GPU explicitly
    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False)
    cap = cv2.VideoCapture(video_path)
    keypoints = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        if results.pose_landmarks:
            landmarks = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in results.pose_landmarks.landmark
            ]
            keypoints.append(landmarks)

    cap.release()
    return keypoints

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
