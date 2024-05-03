from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from process_video import process_video
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    input_language = request.form['input_language']
    target_language = request.form['target_language']
    file = request.files['video_file']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        result_html = process_video(file_path, input_language=input_language, target_language=target_language)
        return result_html

if __name__ == "__main__":
    app.run(debug=True)
