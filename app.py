import os
import json
import cv2
import requests
from flask import Flask, request, jsonify, render_template_string
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

    # Check video duration
    cap = cv2.VideoCapture(filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frames / fps if fps else 0
    cap.release()

    if duration > 4:
        os.remove(filename)
        return "Video too long. Max 4 seconds.", 400

    try:
        keypoints = extract_pose(filename)
        os.remove(filename)
        res = requests.post(WEBHOOK_URL, json={"keypoints": keypoints})
        return jsonify({"status": "success", "webhook_code": res.status_code}), 200
    except Exception as e:
        os.remove(filename)
        return f"Error processing video: {str(e)}", 500

def extract_pose(video_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, smooth_landmarks=True)
    cap = cv2.VideoCapture(video_path)
    keypoints_all = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            keypoints = [
                {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                for lm in results.pose_landmarks.landmark
            ]
            keypoints_all.append(keypoints)

    cap.release()
    return keypoints_all

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
