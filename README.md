# Advance Company Management System

A comprehensive full-stack web application for managing company member contributions, beneficiaries, documents, and financial reports.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [User Guide](#user-guide)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Advance Company Management System is a modern web application designed to streamline member management, financial tracking, beneficiary management, and document handling for companies and organizations.

### Key Capabilities

- **User Management**: Role-based access control (Admin/User)
- **Financial Management**: Track deposits, contributions, and interest calculations
- **Beneficiary Management**: Add and manage beneficiaries with document verification
- **Document Centre**: Upload, categorize, and verify important documents
- **Applications**: Submit and manage entry/exit applications
- **Reports**: Generate financial and activity reports
- **Real-time Notifications**: Stay updated with system activities

---

## ✨ Features

### For Users

- **Dashboard**: Overview of contributions, deposits, and beneficiaries
- **Financial Tracking**: 
  - Make deposits via M-Pesa, Bank Transfer, or Mansa-X
  - View transaction history
  - Track interest earned
- **Beneficiary Management**:
  - Add multiple beneficiaries
  - Upload supporting documents
  - Track verification status
- **Document Management**:
  - Upload identity documents
  - Store birth/death certificates
  - Organize documents by category
- **Applications**:
  - Submit entry/exit applications
  - Track application status
  - View admin feedback

### For Administrators

- **User Management**: View and manage all users
- **Application Review**: Approve or reject applications
- **Document Verification**: Verify uploaded documents
- **Report Generation**: Generate system-wide reports
- **Dashboard Analytics**: System-wide metrics and insights

---

## 🛠 Tech Stack

### Backend (Django REST Framework)

- **Framework**: Django 4.2.7
- **API**: Django REST Framework 3.14.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL
- **Task Queue**: Celery 5.3.4 with Redis
- **PDF Generation**: ReportLab 4.0.7
- **File Storage**: Django FileField (with optional S3 support via boto3)

### Frontend (Angular)

- **Framework**: Angular 18
- **UI**: Tailwind CSS 3.4
- **HTTP Client**: Angular HttpClient
- **Routing**: Angular Router
- **Forms**: Reactive Forms
- **State Management**: RxJS

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│              Angular 18 + Tailwind CSS                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Dashboard │ │Financial │ │Documents │ │Settings  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP/REST API
                         │ JWT Authentication
┌────────────────────────▼─────────────────────────────────────┐
│                        Backend                               │
│         Django REST Framework + PostgreSQL                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Auth    │ │Financial │ │Documents │ │ Reports  │      │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────────────────────────────────────────────┐       │
│  │              PostgreSQL Database                  │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────────────────────────────────────────┐       │
│  │     Celery + Redis (Background Tasks)            │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

### Required Software

- **Python**: 3.8 or higher
- **Node.js**: 18.x or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6.0 or higher (for Celery tasks)
- **npm**: 9.x or higher

### System Requirements

- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/advance-company.git
cd advance-company
```

### 2. Backend Setup

#### a. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### b. Install Dependencies

```bash
pip install -r requirements.txt
```

#### c. Install PostgreSQL

**Windows:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Install and note the password you set

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### d. Create Database

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE advance_company_db;
CREATE USER postgres WITH PASSWORD 'your_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'Africa/Nairobi';
GRANT ALL PRIVILEGES ON DATABASE advance_company_db TO postgres;
\q
```

#### e. Install Redis

**Windows:**
- Download from [Redis Windows](https://github.com/microsoftarchive/redis/releases)
- Extract and run `redis-server.exe`

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu):**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

---

## ⚙️ Configuration

### Backend Configuration

Create `.env` file in `backend/` directory:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=advance_company_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:4200

# Email (Optional - for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

### Frontend Configuration

Update `frontend/src/app/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  apiTimeout: 30000
};
```

---

## 🏃 Running the Application

### Backend

#### 1. Apply Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

#### 2. Create Admin User

```bash
python manage.py create_admin
# Or manually:
python manage.py createsuperuser
```

**Default Admin Credentials** (if using create_admin command):
- Email: `admin@advancecompany.com`
- Password: `admin123`

#### 3. Start Django Server

```bash
python manage.py runserver
```

Server will run at: `http://localhost:8000`

#### 4. Start Celery Worker (Optional - for background tasks)

Open a new terminal:

```bash
cd backend
# Windows
celery -A advance_company worker -l info --pool=solo

# macOS/Linux
celery -A advance_company worker -l info
```

#### 5. Start Celery Beat (Optional - for scheduled tasks)

Open another terminal:

```bash
cd backend
celery -A advance_company beat -l info
```

### Frontend

```bash
cd frontend
npm start
# or
ng serve
```

Application will run at: `http://localhost:4200`

---

## 📚 API Documentation

### Base URL

```
http://localhost:8000/api
```

### Authentication

All protected endpoints require JWT authentication:

```bash
Authorization: Bearer <access_token>
```

### Key Endpoints

#### Authentication

```http
POST /auth/users/register/
POST /auth/users/login/
POST /token/refresh/
GET  /auth/users/me/
PUT  /auth/users/update_profile/
```

#### Financial

```http
GET  /financial/accounts/my_account/
GET  /financial/deposits/
POST /financial/deposits/
POST /financial/deposits/{id}/confirm_payment/
GET  /financial/deposits/monthly_summary/
```

#### Beneficiaries

```http
GET    /beneficiary/
POST   /beneficiary/
GET    /beneficiary/{id}/
PUT    /beneficiary/{id}/
DELETE /beneficiary/{id}/
POST   /beneficiary/{id}/verify/
POST   /beneficiary/{id}/mark_deceased/
```

#### Documents

```http
GET    /documents/
POST   /documents/
DELETE /documents/{id}/
POST   /documents/{id}/verify/
POST   /documents/{id}/reject/
```

#### Applications

```http
GET  /applications/
POST /applications/
POST /applications/{id}/approve/
POST /applications/{id}/reject/
POST /applications/{id}/review/
```

#### Reports

```http
GET  /reports/
POST /reports/generate_financial_report/
GET  /reports/dashboard_summary/
```

---

## 👤 User Guide

### First Time Login

1. Navigate to `http://localhost:4200`
2. Click "Register" and create an account
3. Fill in all required information
4. Login with your credentials

### Making a Deposit

1. Navigate to **Financial** section
2. Click "Make Deposit"
3. Enter amount and select payment method
4. For M-Pesa: Enter phone number
5. Click "Submit Deposit"
6. Wait for payment confirmation

### Adding a Beneficiary

1. Go to **Beneficiary** section
2. Click "Add Beneficiary"
3. Fill in beneficiary details
4. Upload required documents
5. Submit for verification

### Uploading Documents

1. Navigate to **Documents**
2. Click "Upload Document"
3. Select category
4. Choose file (PDF, JPG, PNG)
5. Submit

### Submitting an Application

1. Go to **Applications**
2. Click "New Application"
3. Select type (Entry/Exit)
4. Provide detailed reason
5. Attach supporting documents
6. Submit

---

## 💻 Development

### Backend Development

#### Project Structure

```
backend/
├── advance_company/          # Main project directory
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   └── celery.py            # Celery configuration
├── apps/                    # Django apps
│   ├── accounts/            # User management
│   ├── financial/           # Financial operations
│   ├── beneficiary/         # Beneficiary management
│   ├── documents/           # Document handling
│   ├── applications/        # Application processing
│   └── reports/             # Report generation
├── media/                   # Uploaded files
├── staticfiles/             # Static files
└── manage.py               # Django management
```

#### Adding New Features

1. Create new app:
```bash
python manage.py startapp app_name
```

2. Add to `INSTALLED_APPS` in `settings.py`

3. Create models in `models.py`

4. Create serializers in `serializers.py`

5. Create views in `views.py`

6. Register URLs in `urls.py`

7. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Frontend Development

#### Project Structure

```
frontend/src/
├── app/
│   ├── core/                    # Core functionality
│   │   ├── guards/             # Route guards
│   │   ├── interceptors/       # HTTP interceptors
│   │   ├── models/             # TypeScript interfaces
│   │   └── services/           # API services
│   ├── features/               # Feature modules
│   │   ├── auth/              # Authentication
│   │   ├── dashboard/         # Dashboard
│   │   ├── financial/         # Financial management
│   │   ├── beneficiary/       # Beneficiary management
│   │   ├── documents/         # Document management
│   │   ├── applications/      # Applications
│   │   ├── reports/           # Reports
│   │   ├── settings/          # User settings
│   │   └── support/           # Help & support
│   ├── shared/                # Shared components
│   │   ├── components/        # Reusable components
│   │   └── pipes/             # Custom pipes
│   └── app.routes.ts          # Application routes
├── environments/              # Environment configs
└── styles.scss               # Global styles
```

#### Adding New Components

```bash
ng generate component features/feature-name/component-name --standalone
```

#### Adding New Services

```bash
ng generate service core/services/service-name
```

---

## 🚢 Deployment

### Backend Deployment (Production)

#### 1. Update Settings

Create `backend/advance_company/settings_prod.py`:

```python
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = BASE_DIR / 'mediafiles'
MEDIA_URL = '/media/'

# Database - use production credentials
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PROD_DB_NAME'),
        'USER': config('PROD_DB_USER'),
        'PASSWORD': config('PROD_DB_PASSWORD'),
        'HOST': config('PROD_DB_HOST'),
        'PORT': config('PROD_DB_PORT'),
    }
}
```

#### 2. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 3. Configure Web Server (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/backend/staticfiles/;
    }

    location /media/ {
        alias /path/to/backend/mediafiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 4. Use Gunicorn

```bash
pip install gunicorn
gunicorn advance_company.wsgi:application --bind 0.0.0.0:8000
```

### Frontend Deployment

#### 1. Build for Production

```bash
cd frontend
ng build --configuration production
```

#### 2. Configure Nginx

```nginx
server {
    listen 80;
    server_name your-frontend-domain.com;
    root /path/to/frontend/dist/advance-company-frontend/browser;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### Backend Issues

**Issue**: `django.db.utils.OperationalError: could not connect to server`

**Solution**:
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

**Issue**: `ModuleNotFoundError: No module named 'rest_framework'`

**Solution**:
```bash
pip install -r requirements.txt
```

**Issue**: Celery worker not starting

**Solution**:
- Verify Redis is running
- Check Celery configuration in `celery.py`
- On Windows, use `--pool=solo` flag

#### Frontend Issues

**Issue**: `Cannot find module '@angular/core'`

**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

**Issue**: API calls returning 401 Unauthorized

**Solution**:
- Check token in localStorage
- Verify token hasn't expired
- Re-login to get new token

**Issue**: CORS errors

**Solution**:
- Verify `CORS_ALLOWED_ORIGINS` in backend settings
- Ensure frontend URL is included
- Check browser console for specific error

### Performance Issues

**Slow page loads**:
- Enable production build
- Optimize images
- Use lazy loading
- Enable caching

**Slow API responses**:
- Add database indexes
- Use select_related() and prefetch_related()
- Enable query caching
- Scale database

---

## 📝 Additional Resources

### Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Angular Documentation](https://angular.io/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Support

For issues and questions:
- Email: support@advancecompany.com
- Phone: +254 700 000 000

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 👥 Contributors

- Development Team at Advance Company
- [Your Name] - Lead Developer

---

## 🎉 Acknowledgments

- Django and Angular communities
- Open source contributors
- Beta testers and early users

---

**Last Updated**: January 2026
**Version**: 1.0.0