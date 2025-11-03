# CXR QC Backend (FastAPI)

This directory contains a minimal FastAPI backend for the Medical Dashboard prototype. It provides authentication (JWT), scan records, image uploads, simulated QC analysis, report generation (PDF) and analytics endpoints.

Quick start (Windows PowerShell):

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Seed the database (creates admin / password)

```powershell
python seed.py
```

4. Run the server

```powershell
uvicorn main:app --reload --port 8000
```

Default credentials: admin / password

Notes:
- For production, rotate the `SECRET_KEY` and use proper TLS.
- OAuth2 flows and RBAC are simplified for the prototype.
