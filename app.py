import os
import requests
import tempfile
from flask import Flask, request, jsonify, render_template_string

REPLICATE_API_TOKEN = "r8_2NW7SKL758t9ryFGudlMlW7c6i4d0JI3mUgD5"
REPLICATE_MODEL = "vegetebird/human-pose-estimation"

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_HTML = '''
<!doctype html>
<title>Upload Video</title>
<h1>Upload Swing Video (.mp4)</h1>
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
    if 'video' not in request.files:
        return "No video file provided", 400

    file = request.files['video']
    if not file.filename.endswith('.mp4'):
        return "Only .mp4 videos are supported", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        # Upload video to file.io to generate public URL for Replicate
        with open(filepath, "rb") as f:
            upload_res = requests.post("https://file.io", files={"file": f})
        upload_json = upload_res.json()

        if not upload_json.get("success"):
            return "Failed to upload video to file.io", 500

        video_url = upload_json["link"]

        # Call Replicate
        replicate_res = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "fda41cc8b27645a58ac287b338841f7f50183de1bc26518df315bcbfb62d2995",
                "input": {
                    "video": video_url
                }
            }
        )

        prediction = replicate_res.json()
        return jsonify(prediction), 200

    except Exception as e:
        return f"Error during processing: {e}", 500
    finally:
        os.remove(filepath)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
