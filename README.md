# Bloom Jobs - Django Job Portal

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)

A production-ready Applicant Tracking System (ATS) and Job Portal built with Django. Designed with enterprise-grade security, database optimization, and an AI-powered resume analysis engine powered by Google Gemini.

## ✨ Features

- **Robust Authentication & Roles**: Custom user models for Job Seekers and Employers.
- **Premium Applicant Tracking (ATS)**: Track application statuses from "Applied" to "Hired".
- **AI Resume Analyzer**: Integrated with Gemini 1.5 Pro to provide actionable resume feedback, ATS scoring, and targeted job-matching recommendations.
- **Security Hardened**: Protected against CSRF, XSS, and IDOR vulnerabilities. Enforces strict file-header magic-number validation for PDF/Image uploads.
- **Highly Optimized**: N+1 queries eliminated via extensive `select_related` and `prefetch_related` architecture. Features scalable pagination for large datasets.
- **Production Ready**: Configured for Render deployment with PostgreSQL, WhiteNoise for static files, and `dj-database-url` integration.

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.x, Django 6.0
- **Database**: PostgreSQL (Production via `psycopg`), SQLite (Local Development)
- **Static File Serving**: WhiteNoise (`CompressedManifestStaticFilesStorage`)
- **AI Engine**: Google Gen AI SDK (`google-genai`)
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism design system), Bootstrap Icons

## 🚀 Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/job-portal.git
   cd job-portal
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory (where `manage.py` is):
   ```env
   DEBUG=True
   SECRET_KEY=your-local-secret-key
   GOOGLE_API_KEY=your-google-api-key
   GEMINI_MODEL=gemini-1.5-pro
   ```

5. **Apply Migrations & Run Server**
   ```bash
   python manage.py migrate
   python manage.py runserver 8006
   ```

## ☁️ Production Deployment (Render)

This project is fully configured for zero-downtime deployment on [Render](https://render.com).

1. Create a new **Web Service** on Render and connect this repository.
2. Under the **Build Command**, Render will automatically execute the included script:
   ```bash
   ./build.sh
   ```
3. Under the **Start Command**, enter:
   ```bash
   gunicorn jobportal.wsgi:application
   ```
4. **Environment Variables Required in Render:**
   - `DEBUG`: `False`
   - `SECRET_KEY`: A highly secure, random 50-character string.
   - `DATABASE_URL`: Render's internal PostgreSQL connection string.
   - `ALLOWED_HOSTS`: Your Render URL (e.g., `your-app.onrender.com`).
   - `CSRF_TRUSTED_ORIGINS`: `https://your-app.onrender.com`
   - `GOOGLE_API_KEY`: Your production Google API Key.
   - `GEMINI_MODEL`: `gemini-1.5-pro`

### Note on Media Files in Production
Render provides ephemeral file storage. Any user avatars or resumes uploaded will disappear upon the next deploy unless a persistent disk is attached. For true scalable production, update the `STORAGES` dictionary in `settings.py` to point to **AWS S3** using `django-storages` and `boto3`.

## 🛡️ Security Audit
The platform relies on stringent server-side validations:
- **File Integrity**: Extensions are not trusted. Raw bytes are checked to confirm accurate PDF and JPEG headers.
- **Enforced POST**: State-changing endpoints (like Withdrawing Applications) strictly reject GET requests.
- **Object-Level Permissions**: Employers can only view applications sent to their jobs. Candidates can only access their own AI Analysis.

## 🤝 Contributing
Pull requests are welcome! Please ensure any new views maintain the established query optimizations (avoiding N+1) and utilize standard Django messaging for error handling.

#RUNNING COMMAND
.\env_jobportal\Scripts\activate
python manage.py runserver 8006
8006 LOCALHOST
