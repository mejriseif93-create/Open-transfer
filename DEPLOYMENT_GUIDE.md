# 🚀 SecureShare - Deployment & Production Guide

## Complete Setup for Production

---

## Part 1: Environment Setup

### Local Development

```bash
# 1. Clone/setup project
cd /path/to/secureshare
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
streamlit run secureshare_app.py

# 4. Access at http://localhost:8501
```

### Docker Setup (Recommended)

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY secureshare_app.py .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501 || exit 1

# Run app
CMD ["streamlit", "run", "secureshare_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--logger.level=info"]
```

Build and run:
```bash
docker build -t secureshare:latest .
docker run -d \
  --name secureshare \
  -p 8501:8501 \
  -e STREAMLIT_SERVER_HEADLESS=true \
  secureshare:latest
```

---

## Part 2: Cloud Deployment

### Option A: Streamlit Cloud (Easiest)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/secureshare
   git push origin main
   ```

2. **Connect to Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"
   - Select repository and `secureshare_app.py`
   - Click Deploy

3. **Configure**
   - App URL: secureshare.streamlit.app
   - Settings → Advanced → Add custom domain

### Option B: Heroku (Free Tier Ending)

```bash
# 1. Create Heroku app
heroku create secureshare-app

# 2. Create Procfile
echo "web: streamlit run secureshare_app.py" > Procfile

# 3. Set config
heroku config:set \
  STREAMLIT_SERVER_PORT=8501 \
  STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  STREAMLIT_SERVER_HEADLESS=true

# 4. Deploy
git push heroku main

# 5. Monitor
heroku logs --tail
```

### Option C: AWS (Scalable)

#### Using Elastic Container Service (ECS)

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name secureshare

# 2. Build and push image
docker build -t secureshare .
docker tag secureshare:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/secureshare:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/secureshare:latest

# 3. Create ECS task definition (task-definition.json)
# 4. Create ECS service
# 5. Point ALB to ECS service
```

#### Using EC2

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i key.pem ubuntu@ec2-instance-ip

# 3. Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip nginx

# 4. Setup app
git clone https://github.com/yourusername/secureshare
cd secureshare
pip3 install -r requirements.txt

# 5. Create systemd service
sudo nano /etc/systemd/system/secureshare.service
```

Create `/etc/systemd/system/secureshare.service`:
```ini
[Unit]
Description=SecureShare Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/secureshare
ExecStart=/usr/bin/python3 -m streamlit run secureshare_app.py \
  --server.port=8501 \
  --server.address=127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable secureshare
sudo systemctl start secureshare
sudo systemctl status secureshare
```

### Option D: DigitalOcean App Platform (Easiest VPS)

1. **Connect GitHub repository**
2. **Create new app**
3. **Select Python/Streamlit buildpack**
4. **Configure environment variables**
5. **Deploy**

### Option E: Google Cloud Run (Serverless)

```bash
# 1. Create project
gcloud projects create secureshare

# 2. Build container
gcloud builds submit --tag gcr.io/secureshare/secureshare

# 3. Deploy to Cloud Run
gcloud run deploy secureshare \
  --image gcr.io/secureshare/secureshare \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Part 3: Domain & SSL Setup

### Using Cloudflare (Recommended)

1. **Point domain to Cloudflare**
   - Update NS records at registrar
   - Add DNS record pointing to your app

2. **Enable SSL/TLS**
   - Cloudflare dashboard → SSL/TLS → Flexible

3. **Enable caching**
   - Caching Rules → Cache everything

4. **Setup DDoS protection**
   - WAF Rules → Enable

### Using Let's Encrypt (Self-hosted)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d secureshare.app

# Auto-renew
sudo certbot renew --dry-run
```

---

## Part 4: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/secureshare`:

```nginx
upstream streamlit {
    server 127.0.0.1:8501;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name secureshare.app;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name secureshare.app;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/secureshare.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/secureshare.app/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
    gzip_min_length 1000;

    # Logging
    access_log /var/log/nginx/secureshare_access.log;
    error_log /var/log/nginx/secureshare_error.log;

    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    # Upload size
    client_max_body_size 500M;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints (if added)
    location /api/ {
        proxy_pass http://streamlit;
        limit_req zone=api_limit burst=5 nodelay;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/secureshare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Part 5: Monitoring & Logging

### Setup Prometheus Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'secureshare'
    static_configs:
      - targets: ['localhost:8501']
```

### Setup Centralized Logging (ELK Stack)

```bash
# Install Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.15.0-linux-x86_64.tar.gz
tar xzf filebeat-7.15.0-linux-x86_64.tar.gz
cd filebeat-7.15.0-linux-x86_64

# Configure filebeat.yml to send logs to Elasticsearch
sudo systemctl start filebeat
```

### Application Logging

Update `secureshare_app.py` to add:

```python
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/secureshare/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Log events
logger.info(f"File uploaded: {file_name} ({file_size} bytes)")
logger.info(f"File encrypted successfully")
logger.error(f"Decryption failed: {error}")
```

---

## Part 6: CI/CD Pipeline

### GitHub Actions Setup

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Streamlit Cloud
        run: |
          # Streamlit will auto-deploy on push to main
          echo "Deploying to production..."
```

### Docker Build & Push

```yaml
name: Build and Push Docker Image

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/setup-buildx-action@v1
      - uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v2
        with:
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/secureshare:latest
```

---

## Part 7: Performance Optimization

### Caching Strategy

Add to `secureshare_app.py`:

```python
import streamlit as st
from functools import lru_cache

@st.cache_data
def expensive_computation(x):
    # Won't recompute if same inputs
    return x * 2

@st.cache_resource
def init_connection():
    # Initialize once per session
    return SomeExpensiveResource()
```

### Database Optimization (Future)

```python
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@db.example.com:5432/secureshare',
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## Part 8: Backup & Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup database
pg_dump secureshare_db > /backups/db-$(date +%Y%m%d).sql

# Backup uploaded files
tar -czf /backups/files-$(date +%Y%m%d).tar.gz /var/data/secureshare

# Upload to S3
aws s3 cp /backups/ s3://secureshare-backups/ --recursive
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

### Recovery Procedure

```bash
# Restore database
psql secureshare_db < /backups/db-20240101.sql

# Restore files
tar -xzf /backups/files-20240101.tar.gz -C /
```

---

## Part 9: Security Hardening

### Environment Variables

Create `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost/secureshare
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=secureshare.app,www.secureshare.app
```

Load in app:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
```

### Security Checklist

- [ ] Enable HTTPS/SSL (Let's Encrypt)
- [ ] Set security headers (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Input validation on all fields
- [ ] SQL injection prevention (use ORMs)
- [ ] XSS protection enabled
- [ ] CSRF tokens on forms
- [ ] File upload size limits
- [ ] Temporary files cleanup
- [ ] Secrets not in code (use env vars)
- [ ] Regular security audits
- [ ] Dependency scanning (Snyk)
- [ ] Container scanning (Trivy)
- [ ] WAF enabled (Cloudflare/AWS)

---

## Part 10: Monitoring & Alerts

### Setup Uptime Monitoring

```bash
# Using Uptime Robot (free)
# Configure notification for downtime
# Check every 5 minutes
```

### Setup Error Alerts

Add to app:

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(error_message):
    msg = MIMEText(f"Error in SecureShare: {error_message}")
    msg['Subject'] = "SecureShare Error Alert"
    msg['From'] = "alerts@secureshare.app"
    msg['To'] = "admin@secureshare.app"
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login("alerts@secureshare.app", os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)

try:
    # Your code
    pass
except Exception as e:
    logger.error(f"Critical error: {e}")
    send_alert(str(e))
```

---

## Part 11: Scaling Strategy

### Horizontal Scaling

```yaml
# docker-compose.yml for multiple instances
version: '3'

services:
  web:
    image: secureshare:latest
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://...
    ports:
      - "8501-8503:8501"

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Load Balancing

```nginx
upstream secureshare_cluster {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    location / {
        proxy_pass http://secureshare_cluster;
        # Load balancing
        proxy_next_upstream error timeout invalid_header http_500 http_502;
    }
}
```

---

## Part 12: Cost Estimation

### Monthly Costs (Small Scale, 10K users)

| Service | Cost | Notes |
|---------|------|-------|
| **Streamlit Cloud** | $0-100 | Free tier or paid |
| **Database** | $10-50 | Managed Postgres |
| **Storage** | $10-20 | S3 or similar |
| **CDN** | $5-20 | Cloudflare or CloudFront |
| **Monitoring** | $0-50 | Datadog, Sentry, etc. |
| **Domain** | $12 | Annual |
| **Email** | $10-20 | SendGrid or similar |
| **Total** | **$47-272** | Varies |

### Scaling to 1M users

| Service | Cost | Notes |
|---------|------|-------|
| **Application Servers** | $200-500 | Multiple EC2/containers |
| **Database** | $100-500 | RDS Multi-AZ |
| **Storage** | $100-300 | S3 with replication |
| **CDN** | $100-500 | CloudFront/Cloudflare |
| **Monitoring** | $50-200 | Comprehensive monitoring |
| **Security** | $50-300 | WAF, DDoS protection |
| **Operations** | $1000-5000 | DevOps team |
| **Total** | **$1600-7300+** | Per month |

---

## Quick Start Checklist

- [ ] App runs locally (`streamlit run secureshare_app.py`)
- [ ] Docker image builds (`docker build -t secureshare .`)
- [ ] Tests pass (`pytest`)
- [ ] Code is linted (`pylint`, `black`)
- [ ] Security scan passes (`bandit`)
- [ ] README complete
- [ ] LICENSE added
- [ ] GitHub repo created
- [ ] CI/CD configured
- [ ] Deployed to staging
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Monitoring enabled
- [ ] Backups scheduled
- [ ] Production deployment complete!

---

**You're ready to go live! 🚀**
