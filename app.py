from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import requests
from urllib.parse import urlparse
import magic
import time
from flask_cors import CORS
import argparse
import logging
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Logging configuration
logging.basicConfig(
    filename='/var/log/image_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = '/var/www/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check and create upload directory
upload_dir = Path(UPLOAD_FOLDER)
upload_dir.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image(file_path):
    mime = magic.Magic(mime=True)
    file_mime = mime.from_file(file_path)
    return file_mime.startswith('image/')

def generate_unique_filename(original_filename):
    base, ext = os.path.splitext(original_filename)
    timestamp = str(int(time.time()))
    return f"{base}_{timestamp}{ext}"

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("Received upload request")
        if 'url' in request.json:
            # URL upload
            url = request.json['url']
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            if not original_filename:
                original_filename = 'image.jpg'
            
            filename = generate_unique_filename(secure_filename(original_filename))
            
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return jsonify({'error': 'Failed to download file from URL'}), 400
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if not is_valid_image(file_path):
                os.remove(file_path)
                return jsonify({'error': 'Uploaded file is not an image'}), 400
                
        elif 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            if file and allowed_file(file.filename):
                filename = generate_unique_filename(secure_filename(file.filename))
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                if not is_valid_image(file_path):
                    os.remove(file_path)
                    return jsonify({'error': 'Uploaded file is not an image'}), 400
            else:
                return jsonify({'error': 'File type not allowed'}), 400
        else:
            return jsonify({'error': 'No file or URL found'}), 400
        
        logger.info(f"File successfully uploaded: {filename}")
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'{os.getenv("BASE_URL")}/images/{filename}'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_images():
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                files.append({
                    'name': filename,
                    'url': f'/images/{filename}',
                    'size': os.path.getsize(file_path),
                    'created': os.path.getctime(file_path)
                })
        return jsonify({
            'success': True,
            'files': sorted(files, key=lambda x: x['created'], reverse=True)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    
    logger.info(f"Starting server on port {args.port}")
    app.run(host='127.0.0.1', port=args.port) 