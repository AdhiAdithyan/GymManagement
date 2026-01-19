# Production Deployment Guide: Gym Management System

This guide outlines the steps to deploy your Django Gym Management application on a standard **Ubuntu VPS** (DigitalOcean, AWS, Linode) using **Nginx**, **Gunicorn**, and **PostgreSQL**.

---

## 1. Initial Server Setup

Login to your server and install required system packages:

```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib libpq-dev certbot python3-certbot-nginx -y
```

## 2. Database Setup (PostgreSQL)

Login to PostgreSQL and create your database:

```bash
sudo -u postgres psql
```

Inside the PSQL prompt:
```sql
CREATE DATABASE gym_db;
CREATE USER gym_user WITH PASSWORD 'your_strong_password';
ALTER ROLE gym_user SET client_encoding TO 'utf8';
ALTER ROLE gym_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gym_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE gym_db TO gym_user;
\q
```

## 3. Application Setup

1. **Clone your code** to the server (e.g., `/home/ubuntu/gym_management`).
2. **Create a Virtual Environment**:
   ```bash
   cd /home/ubuntu/gym_management
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```
3. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```ini
   DEBUG=False
   SECRET_KEY=your-auto-generated-secret-key
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,*.yourdomain.com
   DATABASE_URL=postgres://gym_user:your_strong_password@localhost:5432/gym_db
   # Twilio Config
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

## 5. Gunicorn Configuration

Create a Systemd service file for Gunicorn:
`sudo nano /etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/gym_management
ExecStart=/home/ubuntu/gym_management/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          gym_management.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable Gunicorn:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 6. Nginx Configuration

Create a new Nginx site configuration:
`sudo nano /etc/nginx/sites-available/gym_management`

```nginx
server {
    listen 80;
    server_name yourdomain.com *.yourdomain.com; # Support subdomains for multi-tenancy

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/ubuntu/gym_management;
    }

    location /media/ {
        root /home/ubuntu/gym_management;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/gym_management /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 7. SSL with Let's Encrypt

Secure your domain with HTTPS:
```bash
sudo certbot --nginx -d yourdomain.com -d *.yourdomain.com
```

## 8. Final App Steps

On the server, run:
```bash
python manage.py collectstatic
python manage.py migrate
python manage.py create_superuser  # If you have the script, otherwise manage.py createsuperuser
```

---

### Key Production Settings to Verify in `settings.py`

1. **Static/Media Roots**:
   ```python
   STATIC_ROOT = BASE_DIR / 'static'  # collectstatic will move files here
   MEDIA_ROOT = BASE_DIR / 'media'
   ```
2. **Security Items**:
   ```python
   SECURE_BROWSER_XSS_FILTER = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_HSTS_SECONDS = 31536000
   ```
