# RiderGuard

RiderGuard is a fare-transparency and dispute-support system for Filipino ride-hailing and delivery riders
(Maxim, MoveIt, Grab and others). Riders log trips, check fares against published commission rates, and keep a
timestamped Dispute Vault of evidence for unfair cancellations and deactivations.

**IT317 / CSIT327 – G2 · Proponent: Kazt Andre S. Ovalo**

## Core feature (Project Development 2): Trip Logger & Fare Checker

Riders log each trip's fare breakdown (gross fare, commission, other deductions, tips, net received, optional
receipt photo). On every save, the **Fare Checker** compares the trip against the admin-managed **reference
commission rate** that was in effect on the trip date and flags the trip when:

1. the commission deducted is higher than the reference rate allows, or
2. the net amount received is lower than *gross − deductions + tips*.

Differences within ₱1.00 or 1% of the gross fare (whichever is larger) are treated as rounding and not flagged.

| Role | What they can do |
|---|---|
| **Rider** | Log, list/filter, view, edit and delete **their own** trips; see the fare check result per trip; see weekly earnings, flagged fares and possible underpayment on the rider dashboard |
| **Admin** | Add, edit and delete reference commission rates (saving re-checks affected trips); view **all** riders' trips and flags read-only; see trip and flag statistics on the admin dashboard |

| Layer | Where |
|---|---|
| Models | `trips/models.py`: `Platform`, `CommissionRate` (FK → Platform, User), `Trip` (FK → User, Platform, CommissionRate) |
| Fare check logic | `trips/fare_check.py` |
| Rider views / URLs / forms | `trips/views.py`, `trips/urls.py` (`/trips/`), `trips/forms.py` |
| Admin views / URLs | `adminpanel/fare_views.py`, `adminpanel/urls.py` (`/panel/rates/`, `/panel/trips/`) |
| Templates | `trips/templates/trips/`, `adminpanel/templates/adminpanel/rate_*.html`, `trip_*.html` |
| Tests | `trips/tests.py` |

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
- python-dotenv for secrets, Pillow for profile photos and receipt images

## Setup

```bash
git clone https://github.com/KaztAndreOvalo/RiderGuard-Ovalo-KaztAndre-G2.git
cd RiderGuard-Ovalo-KaztAndre-G2
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Edit `.env` and set `DJANGO_SECRET_KEY` and your PostgreSQL credentials. For Supabase, use the
connection details from **Project Settings → Database** and set `DB_SSLMODE=require`.

Create the database (local PostgreSQL), then migrate, load demo data and run:

```bash
psql -U postgres -c "CREATE DATABASE riderguard_db;"
python manage.py migrate           # also seeds the platforms (Maxim, MoveIt, Grab, ...)
python manage.py seed_demo         # test accounts + sample reference rates + sample trips
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with a test account:

| Role | Username | Password |
|---|---|---|
| Admin | `demo_admin` | `AdminDemo#2026` |
| Rider | `demo_rider` | `RiderDemo#2026` |

These are test passwords for local grading only. You can also create your own admin with
`python manage.py createsuperuser`; superusers always get the Admin role.

> The sample reference rates created by `seed_demo` are for testing. Admins should replace them with the
> platforms' published commission rates under **Rates** in the admin panel.

## Run the tests

```bash
python manage.py test
```

## Project structure

```
accounts/     custom User model, registration, login/logout, profile, role decorators
dashboard/    rider dashboard + role-based redirect after login
adminpanel/   custom admin panel: dashboard, user management, reference rates, all trips (read-only)
trips/        core feature: Trip Logger + Fare Checker (models, forms, views, fare_check.py, seed_demo)
templates/    base layout, home page, shared partials
static/       CSS and SVG illustrations
docs/         Project Development reports (PDF)
riderguard/   project settings and URLs
```

## Git workflow

- `main`: stable releases only, updated through a Pull Request from `develop`.
- `develop`: integration branch, created from `main`.
- `feature/<name>`: one branch per feature, created from `develop` and merged back through a Pull Request.

Project Development 2 branches: `feature/trip-logger`, `feature/fare-checker`, `feature/pd2-docs`.
Project Development 1 branches: `feature/custom-user-model`, `feature/registration`, `feature/login-logout`,
`feature/role-dashboards`, `feature/custom-admin-panel`, `feature/user-profile`, `feature/tests-and-docs`,
`fix/login-error-message`, `feature/crimson-theme`. Merged branches are kept, not deleted.
