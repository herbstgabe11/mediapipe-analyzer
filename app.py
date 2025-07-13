from flask import Flask, request, render_template_string
import tempfile
import os

app = Flask(__name__)

# HTML upload form
UPLOAD_FORM = """
<!doctype html>
<title>Upload Golf Swing</title>
<h1>Upload a swing video</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=video>
  <input type=submit value=Upload>
</form>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_file = request.files['video']
        if video_file:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                video_path = tmp.name
                video_file.save(video_path)

            # TODO: Analyze with MediaPipe
            # We'll add keypoint analysis next
            os.remove(video_path)
            return "Video received! (analysis coming soon)"
    return render_template_string(UPLOAD_FORM)
