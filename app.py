
from flask import Flask, request, jsonify
import tempfile
import os
import cv2
import mediapipe as mp
import requests
import json

app = Flask(__name__)
mp_pose = mp.solutions.pose

@app.route('/analyze', methods=['POST'])
def analyze_pose():
    data = request.get_json()
    video_url = data.get('video_url')

    if not video_url:
        return jsonify({'error': 'Missing video_url'}), 400

    try:
        # Download video to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        response = requests.get(video_url, stream=True)
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Process video
        cap = cv2.VideoCapture(temp_file.name)
        pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
        frame_data = []
        frame_count = 0

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = [
                    {
                        'index': idx,
                        'x': lm.x,
                        'y': lm.y,
                        'z': lm.z,
                        'visibility': lm.visibility
                    }
                    for idx, lm in enumerate(results.pose_landmarks.landmark)
                ]
                frame_data.append({
                    'frame': frame_count,
                    'landmarks': landmarks
                })
            frame_count += 1

        cap.release()
        os.remove(temp_file.name)

        return jsonify({'pose_data': frame_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "MediaPipe Pose Analyzer is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
