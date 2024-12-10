server {
    listen 80;
    listen 443 ssl;
    server_name img.magicboxpremium.com;

    ssl_certificate /etc/letsencrypt/live/img.magicboxpremium.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/img.magicboxpremium.com/privkey.pem;

    root /var/www/images;
    client_max_body_size 10M;

    # Перенаправлення з HTTP на HTTPS
    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    }

    # API ендпоінт для завантаження
    location /upload {
        proxy_pass http://127.0.0.1:8080/upload;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Ендпоінт для отримання списку зображень
    location /list {
        proxy_pass http://127.0.0.1:8080/list;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Директорія для зображень
    location /images/ {
        alias /var/www/images/;
        try_files $uri $uri/ =404;
        add_header Access-Control-Allow-Origin *;
        add_header Cache-Control "public, max-age=31536000";
        expires 1y;
    }

    access_log /var/log/nginx/img.magicboxpremium.access.log;
    error_log /var/log/nginx/img.magicboxpremium.error.log;
}