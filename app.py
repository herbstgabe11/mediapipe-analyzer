
from flask import Flask, request, jsonify, render_template_string
import mediapipe as mp
import cv2
import tempfile
import os

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Upload Swing Video</title>
<h1>Upload a Swing Video (.mp4)</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file accept="video/mp4">
  <input type=submit value=Upload>
</form>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video = request.files['file']
        if video.filename == '':
            return "No file selected"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            video.save(tmp.name)
            keypoints = analyze_pose(tmp.name)
            os.unlink(tmp.name)
            return jsonify(keypoints)

    return render_template_string(HTML_FORM)

def analyze_pose(video_path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False)
    cap = cv2.VideoCapture(video_path)
    results = []

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)
        if result.pose_landmarks:
            keypoints = [{
                'x': lm.x,
                'y': lm.y,
                'z': lm.z,
                'visibility': lm.visibility
            } for lm in result.pose_landmarks.landmark]
            results.append(keypoints)

    cap.release()
    pose.close()
    return results

if __name__ == '__main__':
    app.run(debug=True)
