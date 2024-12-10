# Img-Host

Simple and efficient image hosting service written in Python using Flask.

## Prerequisites

- Python 3.8+
- Nginx
- systemd (for Linux service)
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ChornyiDev/Img-Host.git
cd Img-Host
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # For Linux/Mac
# or
.venv\Scripts\activate  # For Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create necessary directories and set permissions:
```bash
sudo mkdir -p /var/www/img-host/images
sudo chown -R www-data:www-data /var/www/img-host
sudo chmod 755 /var/www/img-host
sudo chmod 775 /var/www/img-host/images
```

## Configuration

### 1. Environment Variables
Create `.env` file in the project root:
```bash
UPLOAD_FOLDER=/var/www/img-host/images
BASE_URL=https://your-domain.com
```

### 2. Nginx Configuration
Create a new Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/img-host
```

Add the following configuration (adjust domain and paths as needed):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /images/ {
        alias /var/www/img-host/images/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/img-host /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Systemd Service
Create a systemd service file:
```bash
sudo nano /etc/systemd/system/img-host.service
```

Add the following content (adjust paths as needed):
```ini
[Unit]
Description=Img Host Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Img-Host
Environment="PATH=/path/to/Img-Host/.venv/bin"
ExecStart=/path/to/Img-Host/.venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable img-host
sudo systemctl start img-host
```

## Usage Examples

### Upload an Image
```bash
curl -X POST -F "file=@/path/to/image.jpg" https://your-domain.com/upload
```

Response:
```json
{
    "success": true,
    "url": "https://your-domain.com/images/image.jpg"
}
```

### Get Image Information
```bash
curl https://your-domain.com/info/image.jpg
```

Response:
```json
{
    "filename": "image.jpg",
    "size": 12345,
    "created": "2024-01-01 12:00:00",
    "mime_type": "image/jpeg"
}
```

## Security Considerations

1. Always use HTTPS in production
2. Configure proper file upload limits in Nginx
3. Implement authentication if needed
4. Regularly backup the images directory

## Monitoring

Check service status:
```bash
sudo systemctl status img-host
```

View logs:
```bash
sudo journalctl -u img-host -f