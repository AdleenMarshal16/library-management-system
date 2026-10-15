# Athenaeum – Library Management System
Flask + SQLite backend, plain HTML/CSS/JS frontend.

## Run
```
cd backend
python -m venv venv
venv\Scripts\activate          (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Login: admin / admin123 (full access) · staff / staff123 (cannot delete)
The database (backend/library.sqlite) is created and seeded on first run.
Delete that file to reset to the sample data.
