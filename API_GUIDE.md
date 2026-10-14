# Hoplon API Guide

Covers Tasks 1 to 3 (project setup, accounts and roles, employees). This file is updated as each task is completed.

---

## 1. Setup and running

### 1.1 Project layout (backend)
```
backend/
├── .env                 your real settings (never committed)
├── .env.example         template
├── manage.py
├── requirements.txt
├── venv/                virtual environment (never committed)
├── config/              settings.py, urls.py, wsgi.py, asgi.py
├── accounts/            users, roles, login
└── employees/           departments, locations, employees
```

### 1.2 Every time you start work
```
cd /d "D:\projects\Project H O P L O N\backend"
venv\Scripts\activate
python manage.py runserver
```
The prompt must start with `(venv)`. Stop the server with **Ctrl+C**.

### 1.3 Commands you will use often
| Command | What it does |
|---|---|
| `python manage.py check` | Checks the project for mistakes without touching the database |
| `python manage.py makemigrations <app>` | Creates migration files after a model changes |
| `python manage.py migrate` | Applies migrations to the PostgreSQL database |
| `python manage.py createsuperuser` | Creates a Super Admin account |
| `python manage.py test <app>` | Runs the automated tests for one app |
| `python manage.py runserver` | Starts the development server |

Always run `makemigrations` **before** `migrate`.

### 1.4 The `.env` file
```
SECRET_KEY=long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=hoplon
DB_USER=hoplon_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
```
No quotes and no spaces around `=`. Never commit this file or share the password.

### 1.5 Useful addresses (development)
| Address | Purpose |
|---|---|
| `http://127.0.0.1:8000/api/v1/health/` | Quick check that the server is alive |
| `http://127.0.0.1:8000/api/v1/docs/` | Swagger page: try every endpoint in the browser |
| `http://127.0.0.1:8000/api/v1/schema/` | Machine-readable API description (OpenAPI) |
| `http://127.0.0.1:8000/admin/` | Django's built-in admin site |

---

## 2. Authentication

Hoplon uses **JWT tokens**. A login returns two tokens:

| Token | Lifetime | Use |
|---|---|---|
| `access` | 30 minutes | Sent with every request |
| `refresh` | 7 days | Used to get a new access token without logging in again |

Send the access token in a header:
```
Authorization: Bearer <access token>
```

### Login
`POST /api/v1/auth/login/`
```json
{ "username": "Binusha", "password": "your-password" }
```
Response (200):
```json
{
  "refresh": "...",
  "access": "...",
  "user": { "id": 1, "username": "Binusha", "role": "SUPER_ADMIN", "..." : "..." }
}
```
Login is limited to **10 attempts per minute**. Too many attempts return **429**.

### Refresh
`POST /api/v1/auth/refresh/` with `{ "refresh": "<refresh token>" }` returns a new `access` token.

### Using Swagger
1. Open `/api/v1/docs/`.
2. Run **POST /api/v1/auth/login/** with **Try it out** and **Execute**.
3. Copy the `access` value (without quotation marks).
4. Click **Authorize**, paste it, click **Authorize**, then **Close**.
5. When it expires (401), log in again, click **Authorize**, **Logout**, paste the new token, and **Authorize**.

---

## 3. Roles and permissions

| Role | Value | Can do |
|---|---|---|
| Super Admin | `SUPER_ADMIN` | Everything: manage all accounts including Admins |
| Admin | `ADMIN` | Manage User accounts, departments, locations and employees |
| User | `USER` | View own account and own employee record only |

Additional rules:
- Accounts, employees, departments and locations are **never deleted**, only deactivated (`is_active: false`).
- Nobody can deactivate their own account or change their own role.
- Admins can only create or manage accounts with the User role, and can only link User accounts to employees.
- Accounts created by an admin must change their password at first login (`must_change_password: true`).
- Passwords need at least 10 characters and must pass Django's strength checks.

---

## 4. Endpoints (current)

Base address: `http://127.0.0.1:8000/api/v1/`

### 4.1 Auth
| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `auth/login/` | Anyone | Log in, get tokens |
| POST | `auth/refresh/` | Anyone with a refresh token | New access token |
| GET | `auth/me/` | Any logged-in user | Own account |
| POST | `auth/change-password/` | Any logged-in user | Change own password (`old_password`, `new_password`) |

### 4.2 Users (accounts)
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `users/` | Admin, Super Admin | List accounts (Admins see only User accounts) |
| POST | `users/` | Admin, Super Admin | Create an account |
| GET | `users/{id}/` | Admin, Super Admin | One account |
| PUT / PATCH | `users/{id}/` | Admin, Super Admin | Edit an account (names, email, phone, role, `is_active`) |
| POST | `users/{id}/reset-password/` | Admin, Super Admin | Set a temporary password (`new_password`) |

Filters: `?search=`, `?role=ADMIN`, `?is_active=true`, `?ordering=username`.

### 4.3 Departments
| Method | Path | Purpose |
|---|---|---|
| GET / POST | `departments/` | List or create |
| GET / PUT / PATCH | `departments/{id}/` | View or edit |

Body: `{ "name": "IT", "is_active": true }`. A department with active employees cannot be deactivated.

### 4.4 Locations
| Method | Path | Purpose |
|---|---|---|
| GET / POST | `locations/` | List or create |
| GET / PUT / PATCH | `locations/{id}/` | View or edit |

Body: `{ "name": "Head Office", "address": "...", "is_active": true }`. Same deactivation rule as departments.

### 4.5 Employees
| Method | Path | Who | Purpose |
|---|---|---|---|
| GET / POST | `employees/` | Admin, Super Admin | List or create |
| GET / PUT / PATCH | `employees/{id}/` | Admin, Super Admin | View or edit |
| GET | `employees/me/` | Any logged-in user | Employee record linked to your login |

Example body:
```json
{
  "employee_number": "emp-001",
  "first_name": "Binusha",
  "last_name": "Liyanage",
  "designation": "IT Manager",
  "department": 1,
  "location": 1,
  "user": 1
}
```
- Employee numbers are saved in capitals (`emp-001` becomes `EMP-001`) and must be unique.
- `user` links the employee to a login account (optional, one account per employee).
- Inactive departments and locations cannot be chosen for a new or changed employee.
- Filters: `?search=`, `?department=1`, `?location=1`, `?is_active=true`.

### 4.6 Lists and paging
List endpoints return pages of 25 records:
```json
{ "count": 53, "next": "http://.../?page=2", "previous": null, "results": [ ... ] }
```
Use `?page=2` for the next page.

---

## 5. Response codes and what they mean

### 5.1 Success
| Code | Meaning | Example in Hoplon |
|---|---|---|
| **200 OK** | Request worked, data returned | Login, listing employees, editing a record |
| **201 Created** | A new record was created | Creating a department, location, employee or user |
| **204 No Content** | Worked, nothing to return | Not used yet |

### 5.2 Client errors (something in the request needs fixing)
| Code | Meaning | Typical Hoplon cause | What to do |
|---|---|---|---|
| **400 Bad Request** | The data was rejected | Duplicate employee number; missing field; weak password; inactive department chosen; cannot deactivate own account; admin trying to create an Admin | Read the response body. It names the field and the problem |
| **401 Unauthorized** | Not logged in, or the token is missing, invalid or expired | Token older than 30 minutes; no Authorize in Swagger; wrong password at login | Log in again and use the new `access` token |
| **403 Forbidden** | Logged in but not allowed | A normal User opening `users/` or `employees/`; an Admin doing a Super Admin-only action | Use an account with the right role |
| **404 Not Found** | The record or address does not exist | Wrong `id`; no employee linked to your login on `employees/me/`; a mistyped URL | Check the id and address; link an employee to the account |
| **405 Method Not Allowed** | That method isn't supported on this address | `DELETE` on any record (deleting is disabled); `POST` on a detail address | Use the methods listed in section 4 |
| **429 Too Many Requests** | Rate limit reached | More than 10 login attempts in a minute | Wait a minute and try again |

### 5.3 Server errors
| Code | Meaning | What to do |
|---|---|---|
| **500 Internal Server Error** | A bug or unexpected failure on the server | Look at the terminal where `runserver` is running; it shows the full error. Report it with the traceback |

### 5.4 Error body formats
Field problem (400):
```json
{ "employee_number": ["An employee with this number already exists."] }
```
General problem (400):
```json
{ "non_field_errors": ["You cannot deactivate your own account."] }
```
Access problem (401, 403, 404):
```json
{ "detail": "Authentication credentials were not provided." }
```
Invalid or expired token (401):
```json
{ "detail": "Given token not valid for any token type", "code": "token_not_valid" }
```

---

## 6. Testing

Run an app's tests:
```
python manage.py test accounts
python manage.py test employees
```
Expected so far: `accounts` 11 tests OK, `employees` 14 tests OK. Tests use a temporary database that is created and removed automatically, which is why `hoplon_user` needs the **Create databases** permission.

Run all tests before every commit:
```
python manage.py test
```

---

## 7. Troubleshooting (problems met during setup)

| Message | Cause | Fix |
|---|---|---|
| `Python was not found; run without arguments to install from the Microsoft Store` | Windows alias is intercepting `python` | Use `py` instead, or turn off the App execution alias for Python in Settings |
| `The system cannot find the path specified` on `venv\Scripts\activate` | The `venv` folder doesn't exist yet | Create it with `py -m venv venv`, then activate |
| `can't open file '...manage.py': No such file or directory` | Running from the wrong folder, or `manage.py` is missing | `cd` into `backend`, check with `dir` |
| `ModuleNotFoundError: No module named 'config.settings'` | `settings.py` is missing or misnamed, or `config\__init__.py` is missing | Check `dir config`: no space before `.py`, no `.txt` ending, `__init__.py` present |
| Files saved as `something.py.txt` | Notepad added `.txt` | Save with type **All files**, or rename with `ren` |
| `unapplied migration(s)` warning | Database tables not created yet | Run `makemigrations`, then `migrate` |
| `IntegrityError: duplicate key value violates unique constraint` | Data reached the database without a check | Add a validation in the serializer so the API returns 400 instead (this happened with employee numbers and is fixed) |
| Swagger shows only some sections | New app not registered or old files in place | Check `INSTALLED_APPS` and `config\urls.py`, restart the server, press Ctrl+F5 |
| Everything returns 401 in Swagger | Token expired or not authorized | Log in again and re-authorize |
| `password authentication failed for user "hoplon_user"` | `.env` password doesn't match PostgreSQL | Fix `DB_PASSWORD` in `.env`, or `ALTER USER hoplon_user WITH PASSWORD '...'` in pgAdmin |

---

## 8. Git habits

Commit after each finished task, with a clear message:
```
cd /d "D:\projects\Project H O P L O N"
git add .
git commit -m "feat(employees): departments, locations, employee records, tests"
```
Message prefixes used: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `chore` (setup and housekeeping).
Never commit `.env`, `venv`, or uploaded files. `.gitignore` already excludes them.
