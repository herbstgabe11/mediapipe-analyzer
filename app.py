import os
import requests
from flask import Flask, request, jsonify
import tempfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

REPLICATE_API_TOKEN = os.getenv(r8_2NW7SKL758t9ryFGudlMlW7c6i4d0JI3mUgD5)
N8N_WEBHOOK = "https://herbstgabe.app.n8n.cloud/webhook-test/5263ccbb-5c4c-4199-9b9c-a7f0e3329b28"

@app.route("/upload", methods=["POST"])
def upload():
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400

    video = request.files['video']
    temp_path = os.path.join(UPLOAD_FOLDER, video.filename)
    video.save(temp_path)

    # Upload to file.io for public URL
    with open(temp_path, 'rb') as f:
        res = requests.post("https://file.io", files={"file": f})
        if not res.ok:
            return jsonify({"error": "Failed to upload to file.io"}), 500
        fileio_url = res.json().get("link")

    # Send to Replicate
    replicate_res = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": "20c020d2028e0378ffb1d6371a42819d40c69b6ed6c26433ae1c78c00c9ce3e5",  # vegetebird model
            "input": {"video": fileio_url}
        }
    )

    if replicate_res.status_code != 201:
        return jsonify({"error": "Replicate error", "details": replicate_res.text}), 500

    prediction = replicate_res.json()
    prediction_url = prediction.get("urls", {}).get("get")

    # Poll for result
    while True:
        poll = requests.get(prediction_url, headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"})
        poll_data = poll.json()
        if poll_data["status"] == "succeeded":
            keypoints = poll_data["output"]
            break
        elif poll_data["status"] == "failed":
            return jsonify({"error": "Replicate processing failed"}), 500

    # Send to n8n
    requests.post(N8N_WEBHOOK, json={"keypoints": keypoints})

    return jsonify({"status": "complete", "message": "Video processed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
