# 🏥 MediAssist AI — AI Healthcare Management System

A complete, production-ready **AI-powered healthcare management platform** built on
**Flask**, **Bootstrap 5** and an existing **scikit-learn RandomForest symptom
checker**. It combines three role-based dashboards (Patient / Doctor / Admin) with a
conversational **AI Doctor** that collects symptoms, predicts the top-5 likely
conditions with confidence scores, and recommends a specialist and appointment.

> ⚠️ **Educational software, not medical advice.** The ML model is trained on a
> **synthetic dataset** (`data/symptom_disease.csv`) and is not clinically validated.
> It cannot diagnose you. For real health concerns consult a licensed doctor; for
> anything urgent call your local emergency services.

---

## ✨ Features

### 👤 Patients
- Account registration, login/logout, **remember me**, forgot password and (placeholder) email verification
- **AI Doctor Chat** — a conversational symptom checker that asks follow-up questions, builds a structured symptom list, and predicts the top-5 diseases with confidence
- **Disease Prediction** — manual symptom picker with the same model + specialist recommendation
- **Book appointments** — Department → Doctor → Date → Time → Confirm (respects doctor availability)
- Appointment history (pending / accepted / rejected / completed / cancelled)
- Medical history (doctor records + AI prediction history)
- Prescriptions — view, **download as PDF**, print
- Editable profile (name, age, gender, blood group, address, phone, emergency contact)
- In-app notifications & settings (change password, dark mode)

### 🧑‍⚕️ Doctors
- Today's appointments and upcoming schedule
- Accept / reject / complete appointments
- Search patients by name, phone or email; view full patient history
- Write prescriptions (multiple medicines, dosage, frequency, duration, instructions)
- Manage weekly availability and an overall accepting-appointments toggle

### 🛡️ Admin
- Analytics dashboard with **Chart.js** charts (last-7-days trend, per-department, status doughnut)
- Add / delete / toggle doctors
- Manage patients (search, enable / disable accounts)
- Manage appointments (filter + cancel)
- Manage departments (add / edit / delete)

### 🧠 AI Doctor
- Natural-language symptom extraction (53 symptoms, alias matching)
- Triage-style follow-ups: *“Since when?”*, *“Any cough?”*, *“Any headache?”*, *“Difficulty breathing?”*
- Runs the existing RandomForest model → top-5 conditions with **confidence %**
- Recommends a specialist + department and offers to book an appointment
- Always reminds the user it is an **educational assistant, not a licensed doctor**
- Flags potentially serious symptoms

---

## 🚀 Quick start

```bash
# 1. Clone the repository
git clone https://github.com/your-user/medical-assistant.git
cd medical-assistant

# 2. (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://localhost:5000**. The database and seed data are created
automatically on first run (`medical.db`).

> The existing model (`models/classifier.joblib` + `models/symptom_list.joblib`)
> is reused as-is — **no retraining needed**. To retrain with new data, run
> `python train_model.py` (after updating `data/symptom_disease.csv`).

### 🔑 Demo accounts (created automatically)

| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Patient | patient@medassist.local | patient123  |
| Doctor  | arjun@medassist.local   | doctor123   |
| Admin   | admin@medassist.local   | admin123    |

> ⚠️ Change these in `database/seed.py` before going to production.

---

## 🗂️ Folder structure

```
medical-assistant/
├── app.py                    # App factory + entry point (python app.py)
├── wsgi.py                   # WSGI entry for gunicorn / PythonAnywhere
├── config.py                 # Configuration (env-driven, SQLite/PostgreSQL)
├── requirements.txt
├── render.yaml               # Render.com blueprint (web + postgres)
├── Procfile                  # Railway / Render start command
├── .env.example              # Copy to .env and fill in secrets
├── medical.db                # SQLite database (auto-created)
│
├── database/
│   ├── db.py                 # SQLAlchemy instance + SQLite FK pragma
│   ├── seed.py               # First-run seed (admin, departments, demo data)
│   └── __init__.py
│
├── models/                   # SQLAlchemy ORM models
│   ├── user.py               # Users (patient/doctor/admin), auth tokens
│   ├── patient.py            # Patients profile
│   ├── doctor.py             # Doctors profile
│   ├── department.py         # Departments
│   ├── appointment.py        # Appointments
│   ├── medical_history.py    # MedicalHistory
│   ├── prescription.py       # Prescription + PrescriptionItem
│   ├── chat_history.py       # ChatHistory (AI transcripts)
│   ├── notification.py       # Notifications
│   ├── doctor_availability.py# DoctorAvailability (weekly windows)
│   ├── prediction_history.py # AI prediction audit trail
│   ├── classifier.joblib     # ⚙️ Reused RandomForest model (existing)
│   ├── symptom_list.joblib   # ⚙️ Reused 53-feature column list (existing)
│   └── __init__.py
│
├── routes/                   # Blueprints
│   ├── auth.py               # register / login / logout / reset / verify
│   ├── patient.py            # patient dashboard, profile, settings, history
│   ├── doctor.py             # appointments, patients, prescriptions, availability
│   ├── admin.py              # analytics, doctors, patients, appointments, departments
│   ├── ai.py                 # AI chat + prediction APIs and pages
│   ├── appointments.py       # booking wizard + slot API
│   ├── prescriptions.py      # list / detail / PDF download
│   ├── notifications.py      # notification center
│   └── __init__.py
│
├── ai/
│   └── predictor.py          # Reusable wrapper around classifier.joblib (top-5 + confidence)
├── chatbot/
│   ├── engine.py             # Conversational state machine
│   └── symptom_db.py         # Symptom aliases + condition/specialist knowledge
├── appointments/
│   └── slots.py              # Availability-aware time-slot generation
├── prescriptions/
│   └── pdf.py                # ReportLab prescription PDF generator
├── utils/
│   ├── decorators.py         # Role-based access control
│   ├── email.py              # Console/SMTP email (verification, reset)
│   └── helpers.py            # notify(), history helpers
│
├── templates/                # Jinja2 templates (auth, patient, doctor, admin, errors)
├── static/
│   ├── css/style.css         # Theming incl. dark mode
│   ├── js/main.js            # Dark mode toggle, sidebar, alerts
│   └── images/logo.svg
└── data/
    └── symptom_disease.csv   # Training dataset (existing)
```

### Database schema

```
users ── 1:1 ── patients            users ── 1:1 ── doctors ── N:1 ── departments
  │                                       │
  │── N:1 ── notifications                │── N:1 ── doctor_availability
  │── N:1 ── chat_history
patients ── 1:N ── appointments ── N:1 ── doctors
patients ── 1:N ── medical_history ── N:1 ── doctors
patients ── 1:N ── prescriptions ── 1:N ── prescription_items
patients ── 1:N ── prediction_history
```

---

## 🔐 Security

- **Password hashing** with bcrypt (`Flask-Bcrypt`)
- **CSRF protection** on every form (`Flask-WTF` CSRFProtect) — API calls include the token
- **Role-based authorization** — `@patient_required`, `@doctor_required`, `@admin_required` decorators; cross-role pages return 403
- **ORM/prepared statements** throughout (SQLAlchemy) — no string-interpolated SQL
- **Input validation** on registration, login, profile, appointments and prescriptions
- **Session management** via Flask-Login (remember-me cookie, HTTP-only)
- Secret key, mail credentials and DB URL read from environment variables

---

## 📤 Deployment

The app uses `DATABASE_URL` when provided (PostgreSQL) and otherwise falls back to
SQLite — so the same code runs on all three platforms.

### Render.com
1. Push the repo to GitHub.
2. In Render, **New → Blueprint** and select the repo (uses `render.yaml`, which provisions the web service **and** a PostgreSQL database).
3. Render sets `DATABASE_URL` and generates `SECRET_KEY` automatically.
4. Deploy — the app migrates/creates its tables and seeds itself on first boot.

### Railway
1. **New Project → Deploy from GitHub repo**.
2. Add a **PostgreSQL** plugin; Railway sets `DATABASE_URL` automatically.
3. Set `SECRET_KEY` in the service variables.
4. The `Procfile` (`web: gunicorn wsgi:app`) is picked up automatically.

### PythonAnywhere
1. Upload the project (excluding `venv`, `medical.db`).
2. Create a virtualenv: `mkvirtualenv --python=3.11 medassist`, then `pip install -r requirements.txt`.
3. In the **Web** tab create a manual config; WSGI configuration file → point to `wsgi.py` (import `from app import app as application`).
4. Set `SECRET_KEY` (and optionally `DATABASE_URL`) in the WSGI environment; add `static/` as a static URL mapping.

### Production checklist
- Set a strong random `SECRET_KEY`.
- Set `EMAIL_VERIFICATION_REQUIRED=true` and configure `MAIL_*` SMTP vars.
- Point `DATABASE_URL` at a managed PostgreSQL instance.
- Replace the demo seed credentials in `database/seed.py`.

---

## 📸 Screenshots

> Placeholders — add real captures of each screen here.

| | |
|---|---|
| **Login** | ![Login](static/images/screenshot-login.png) |
| **Patient dashboard** | ![Patient](static/images/screenshot-patient.png) |
| **AI Doctor chat** | ![AI chat](static/images/screenshot-ai-chat.png) |
| **Prediction results** | ![Prediction](static/images/screenshot-prediction.png) |
| **Doctor dashboard** | ![Doctor](static/images/screenshot-doctor.png) |
| **Admin analytics** | ![Admin](static/images/screenshot-admin.png) |

---

## 🧠 Machine-learning notes

- The model is a `RandomForestClassifier` (200 trees) trained in `train_model.py` on
  ~800 synthetic rows across **20 common, non-emergency conditions** and **53 binary
  symptom features**.
- `ai/predictor.py` loads the saved artifacts once (process-cached singleton) and
  exposes `predict(symptoms) -> top-5 [{disease, confidence}]`.
- Predictions are logged to `prediction_history` for the patient's history and audit.
- **Swap in a real dataset:** keep one 0/1 column per symptom + a final `condition`
  column in `data/symptom_disease.csv`, then rerun `python train_model.py` and restart
  the app — nothing else changes.

---

## 🧭 Future scope

- [ ] Real SMTP email delivery + resend verification
- [ ] Telemedicine / video-consultation links in appointments
- [ ] Doctor verification with uploaded credentials
- [ ] Two-factor authentication (TOTP)
- [ ] Payments for paid consultations
- [ ] Laboratory test requests and report uploads
- [ ] i18n (multi-language support)
- [ ] Dockerfile + docker-compose
- [ ] Swagger/OpenAPI docs for the REST endpoints

---

## 📜 License

MIT — free to use for education and portfolios. **Not** licensed for clinical use.

---

## ❤️ Acknowledgments

This project reuses the trained `RandomForestClassifier` artifacts produced by the
original *Symptom Checker Assistant* capstone (see `train_model.py` and
`generate_data.py`).
