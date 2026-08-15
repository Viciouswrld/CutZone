# CutZone — Barbershop Booking & Scheduling System

A complete full-stack appointment booking website for **CutZone**, a premium
barbershop in **Owerri, Nigeria**. Built with **Python / Django**, **SQLite**,
**Bootstrap 5** and vanilla **JavaScript**.

Opening hours: **8:00 AM – 7:00 PM** · Currency: **Nigerian Naira (₦)**

---

## Features

**Customers**
- Register, login, logout, change & reset password
- View / edit profile
- Browse and search services & barbers
- Guided booking flow: Service → Barber → Date → Available Time → Confirm
- Automatic time-slot generation (respects service duration, barber schedule,
  shop hours, and existing bookings — no double booking possible)
- View, cancel (with confirmation) and reschedule appointments
- Booking history, printable booking receipt with unique reference (CZ-2026-0001)
- Leave 1–5★ reviews on completed appointments (one review per appointment)

**Administrators** (custom dashboard at `/dashboard/`, staff accounts only)
- Statistics: customers, barbers, services, appointments, revenue, etc.
- Manage appointments: search, filter (date / barber / service / status),
  approve / complete / cancel
- Calendar view (day / week / month)
- Manage customers, barbers (incl. photo upload), services, weekly schedules
- Moderate / delete reviews, read contact messages

**Validation (backend enforced)**
- No double / overlapping bookings (also guarded by a DB unique constraint)
- No bookings in the past, outside shop hours, or beyond a barber's shift
- Duration respected (a 60-min service can't start at 6:30 PM)
- Inactive barbers/services can't be booked

---

## Technology

- Python 3.10+ · Django 5.x · SQLite
- HTML5, CSS3, JavaScript, Bootstrap 5 (CDN)
- Pillow (barber photo uploads)

---

## Setup Instructions

Open a terminal in the `cutzone/` project folder (the one containing
`manage.py`).

### 1. Create and activate a virtual environment

```
python -m venv venv
```

**Windows (Command Prompt):**
```
venv\Scripts\activate
```

**Windows (PowerShell):**
```
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```
source venv/bin/activate
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Set up the database

```
python manage.py makemigrations
python manage.py migrate
```

### 4. Create an admin account (optional if you use the seed data)

```
python manage.py createsuperuser
```

### 5. Load demonstration data (recommended)

```
python manage.py seed_demo
```

This creates:
- 3 services: Haircut ₦3,000/30 min · Haircut + Beard ₦4,500/45 min · Full Package ₦6,000/60 min
- 4 barbers: Victor, Jacob, Emmanuel, John (Mon–Sat 8 AM–7 PM, Sunday off)
- Admin account → username `admin`, password `admin12345`
- Demo customer → username `demo`, password `demo12345`
- Example appointments (completed, cancelled, upcoming) and reviews

The command is safe to run multiple times — it never duplicates data.

### 6. Run the server

```
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

| URL              | Page                                  |
|------------------|---------------------------------------|
| `/`              | Public website                        |
| `/accounts/login/` | Login (customers & admin)           |
| `/dashboard/`    | Custom admin dashboard (staff only)   |
| `/django-admin/` | Django's built-in admin (superusers)  |

---

## Email configuration (optional)

Password-reset emails use Django's **console backend** by default — the email
text is printed in the terminal, so no real provider is needed locally.
To use real SMTP, set environment variables before running the server:

```
CUTZONE_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
CUTZONE_EMAIL_HOST=smtp.example.com
CUTZONE_EMAIL_PORT=587
CUTZONE_EMAIL_USER=you@example.com
CUTZONE_EMAIL_PASSWORD=yourpassword
CUTZONE_EMAIL_TLS=1
```

---

## Project structure

```
cutzone/
├── manage.py
├── requirements.txt
├── cutzone/            # project settings & root URLs
├── core/               # home / about / contact + seed_demo command
├── accounts/           # auth, profile, customer dashboard
├── services/           # Service model + public services page
├── barbers/            # Barber & BarberSchedule models + public page
├── bookings/           # Appointment model, availability engine, booking flow
├── reviews/            # Review model + leave-review flow
├── dashboard/          # custom admin dashboard (staff only)
├── templates/          # all HTML templates (template inheritance)
├── static/             # css / js / images
└── media/              # uploaded barber photos
```

## Running the tests

```
python manage.py test
```

Covers the booking validation rules: double booking, overlap, past dates,
shop hours, inactive barbers/services, and reschedule conflicts.
