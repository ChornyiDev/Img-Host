import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import uuid

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
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Створюємо папку, якщо вона не існує
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image_data, extension):
    # Генеруємо унікальне ім'я файлу
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Відкриваємо зображення
    img = Image.open(image_data)
    
    # Зберігаємо зображення без модифікацій
    if extension.lower() in ['png', 'webp']:
        # Зберігаємо PNG та WebP з прозорістю
        img.save(filepath, format=extension.upper(), quality=100)
    else:
        # Для інших форматів
        if img.mode in ['RGBA', 'LA']:
            # Якщо є прозорість, конвертуємо в RGB зі збереженням прозорості
            background = Image.new('RGBA', img.size, (255, 255, 255, 0))
            background.paste(img, mask=img.split()[-1])
            background.save(filepath, format=extension.upper(), quality=100)
        else:
            # Зберігаємо без змін
            img.save(filepath, format=extension.upper(), quality=100)
    
    return filename

@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    try:
        # Перевірка на наявність файлу або URL
        if 'file' in request.files:
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'File type not allowed'}), 400
            
            # Отримуємо розширення файлу
            extension = file.filename.rsplit('.', 1)[1].lower()
            
            # Зберігаємо файл
            filename = save_image(file, extension)
            
        elif 'url' in request.form:
            url = request.form['url']
            
            # Завантажуємо зображення за URL
            response = requests.get(url)
            if response.status_code != 200:
                return jsonify({'success': False, 'error': 'Failed to fetch image'}), 400
            
            # Визначаємо тип файлу
            content_type = response.headers.get('content-type', '')
            if not any(ext in content_type.lower() for ext in ALLOWED_EXTENSIONS):
                return jsonify({'success': False, 'error': 'Invalid image type'}), 400
            
            # Отримуємо розширення з Content-Type
            extension = content_type.split('/')[-1]
            if extension not in ALLOWED_EXTENSIONS:
                extension = 'jpg'
            
            # Зберігаємо зображення
            filename = save_image(BytesIO(response.content), extension)
            
        else:
            return jsonify({'success': False, 'error': 'No file or URL provided'}), 400
        
        # Формуємо URL для доступу до зображення
        image_url = f"{os.getenv('BASE_URL')}/{filename}"
        
        return jsonify({
            'success': True,
            'url': image_url
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5006) 