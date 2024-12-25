import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import uuid
import shutil

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Конфігурація
UPLOAD_FOLDER = '/var/www/img.magicboxpremium.com'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # Збільшили до 50 MB для відео

# Створюємо папку, якщо вона не існує
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file_data, extension):
    # Генеруємо унікальне ім'я файлу
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if extension.lower() in ALLOWED_VIDEO_EXTENSIONS:
        # Для відео файлів просто копіюємо
        if hasattr(file_data, 'save'):
            file_data.save(filepath)
        else:
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(file_data, f)
    else:
        # Для зображень використовуємо попередню логіку
        img = Image.open(file_data)
        if extension.lower() in ['png', 'webp']:
            img.save(filepath, format=extension.upper(), quality=100)
        else:
            if img.mode in ['RGBA', 'LA']:
                background = Image.new('RGBA', img.size, (255, 255, 255, 0))
                background.paste(img, mask=img.split()[-1])
                background.save(filepath, format=extension.upper(), quality=100)
            else:
                img.save(filepath, format=extension.upper(), quality=100)
    
    return filename

@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' in request.files:
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'File type not allowed'}), 400
            
            # Перевірка розміру файлу
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > MAX_FILE_SIZE:
                return jsonify({'success': False, 'error': 'File too large'}), 400
            
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = save_file(file, extension)
            
        elif 'url' in request.form:
            url = request.form['url']
            
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return jsonify({'success': False, 'error': 'Failed to fetch file'}), 400
            
            content_type = response.headers.get('content-type', '')
            
            # Визначаємо тип файлу
            if 'video/mp4' in content_type:
                extension = 'mp4'
            elif any(ext in content_type.lower() for ext in ALLOWED_IMAGE_EXTENSIONS):
                extension = content_type.split('/')[-1]
                if extension not in ALLOWED_EXTENSIONS:
                    extension = 'jpg'
            else:
                return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
            # Перевірка розміру файлу
            content_length = int(response.headers.get('content-length', 0))
            if content_length > MAX_FILE_SIZE:
                return jsonify({'success': False, 'error': 'File too large'}), 400
            
            filename = save_file(BytesIO(response.content), extension)
            
        else:
            return jsonify({'success': False, 'error': 'No file or URL provided'}), 400
        
        image_url = f"{os.getenv('BASE_URL')}/{filename}"
        
        return jsonify({
            'success': True,
            'url': image_url
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5006) 