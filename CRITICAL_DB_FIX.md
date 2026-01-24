# CRITICAL: Database Persistence Issue

We noticed the server log "Shutting down: Master". This often happens on deployments.
More importantly, your live site is still failing with `OperationalError: no such table: users`.

## 1. The Root Cause (SQLite on Railway)
Your project is currently configured to use **SQLite** (the default local database).
**Railway is an ephemeral file system.**
This means:
1.  Every time you deploy, the file system is wiped.
2.  Every time the server restarts (the "Shutting down" log), the database file (`db.sqlite3`) is **DELETED**.
3.  Even if you run `migrate`, the database will be lost on the next deploy/restart.

## 2. The Fix (Switch to PostgreSQL)
You MUST provision a PostgreSQL database on Railway to have persistent data.

### Step-by-Step Fix:
1.  **Add PostgreSQL**:
    - Go to your Railway Project Dashboard.
    - Click **"New"** -> **"Database"** -> **"PostgreSQL"**.
    - Wait for it to be created.

2.  **Connect Database**:
    - Railway automatically sets the `DATABASE_URL` environment variable.
    - Your `settings.py` already uses `dj_database_url`, so it will **automatically** switch to PostgreSQL once that variable exists!

3.  **Run Migrations (One Last Time)**:
    - Once Postgres is attached, open the Service Console.
    - Run: `python manage.py migrate`
    - Create a superuser: `python manage.py createsuperuser`

Once you do this, your data will persist, and the "no such table" errors will stop forever.
