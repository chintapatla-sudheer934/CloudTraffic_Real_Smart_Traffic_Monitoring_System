# CloudTraffic - Smart Traffic Monitoring System

## Run on Windows

Open PowerShell in this folder.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Open:
http://127.0.0.1:5000

## Login
Email: admin@cloudtraffic.local
Password: Admin@123

The application always opens with the login page first.

## Features
- Login and logout
- Cloud command center
- Live traffic monitoring
- Junction management
- Sensor management
- Traffic prediction
- Congestion alerts
- Analytics
- Audit trail
- REST telemetry API
- SQLite database
- Responsive interface

## Important
`run.py` and `requirements.txt` are in the project root. Do not run `python run.py` from the parent Downloads folder.
