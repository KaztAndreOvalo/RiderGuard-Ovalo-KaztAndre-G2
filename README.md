# RiderGuard

RiderGuard is a fare-transparency and dispute-support system for Filipino ride-hailing and delivery riders
(Maxim, MoveIt, Grab and others). Riders log trips, check fares against published commission rates, and keep a
timestamped Dispute Vault of evidence for unfair cancellations and deactivations.

**IT317 – G2 · Proponent: Kazt Andre S. Ovalo**

## Project Development 1: Account Feature

| Requirement | Where |
|---|---|
| Registration with validation (required fields, email format, unique username/email, password confirmation) | `accounts/forms.py` → `RegistrationForm`, `/accounts/register/` |
| Hashed passwords via Django auth | `UserCreationForm` / `set_password` (PBKDF2) |
| Login (username **or** email) with error message, logout that ends the session | `/accounts/login/`, `/accounts/logout/` (POST) |
| Protected pages redirect to login | `@login_required`, `LOGIN_URL = "accounts:login"` |
| Two roles: **Rider** and **Admin** | `accounts.models.User.role` |
| Role-based dashboards, role-specific navigation | `/dashboard/` → `/dashboard/rider/` or `/panel/` |
| Blocking another role's dashboard by URL | `accounts/decorators.py` → `rider_required`, `admin_required` |
| View and edit own profile (name, email, contact number, photo, vehicle, platforms) | `/accounts/profile/`, `/accounts/profile/edit/` |
| User illustration | `static/img/` (default avatar, rider and admin illustrations) |
| Custom admin panel (Django admin is **not** installed) | `adminpanel` app, `/panel/users/` |

## Tech stack

- Django 5.2 (backend + Django templates)
- PostgreSQL (local PostgreSQL or Supabase); SQLite is not used
- python-dotenv for secrets, Pillow for profile photos

## Setup

```bash
git clone https://github.com/<your-username>/RiderGuard-Ovalo-KaztAndre-G2.git
cd RiderGuard-Ovalo-KaztAndre-G2
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Edit `.env` and set `DJANGO_SECRET_KEY` and your PostgreSQL credentials. For Supabase, use the
connection details from **Project Settings → Database** and set `DB_SSLMODE=require`.

Create the database (local PostgreSQL), then migrate and create the first admin:

```bash
psql -U postgres -c "CREATE DATABASE riderguard_db;"
python manage.py migrate
python manage.py createsuperuser   # becomes an Admin in RiderGuard
python manage.py runserver
```

Open http://127.0.0.1:8000/. Riders register at `/accounts/register/`. Admins log in and go to `/panel/`.

## Run the tests

```bash
python manage.py test
```

## Project structure

```
accounts/     custom User model, registration, login/logout, profile, role decorators
dashboard/    rider dashboard + role-based redirect after login
adminpanel/   custom admin panel (dashboard and user management)
templates/    base layout, home page, shared partials
static/       CSS and SVG illustrations
riderguard/   project settings and URLs
```

## Git workflow

Each feature is built on its own branch and merged into `main` with `--no-ff`, so the history shows every feature:
`feature/custom-user-model`, `feature/registration`, `feature/login-logout`, `feature/role-dashboards`,
`feature/custom-admin-panel`, `feature/user-profile`, `feature/tests-and-docs`.
