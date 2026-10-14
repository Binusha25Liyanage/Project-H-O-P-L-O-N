# Hoplon: Asset Management System

**Project name:** Hoplon (the large round shield of the Greek and Spartan hoplite soldier; symbol of protection)
**Organisation:** Lakmee Exports Lanka (large-scale FMCG)
**Document status:** Living document. Update it as each build task is completed.

---

## 1. Purpose and goals

Hoplon is an internal system to register, assign, track, value and report on every physical asset the company issues to its people.

**Goals**
1. One trusted register of all company assets, separated by category.
2. Always know who holds an asset now, and who held it before.
3. Track condition and value over the asset's life (purchase value vs current value).
4. Let every employee see the assets issued to them.
5. Provide QR-based identification and fast registration from a mobile phone.
6. Produce management reports (category-wise, consumer-wise, lifetime).

**Out of scope for version 1:** procurement/purchase-order workflow, full accounting integration, GPS tracking of vehicles, consumable stock (for example toner).

---

**UI theme:** cherry alloy red, ash and mercury (grey/silver), designed with Stitch AI. Logo idea: round shield with the Spartan lambda (Λ).

---

## 2. Users and roles

| Role | Typical person | Capabilities |
|---|---|---|
| Super Admin | Managing Director, IT Manager | Everything: company-wide dashboards and reports, manage admins, approve disposals/write-offs, view valuations and audit log, system settings |
| Admin | IT Officer | Register and edit assets, upload photos, generate and print QRs, assign/transfer/return assets, log condition and maintenance, manage employees, operational reports |
| User | Any employee | Read-only view of assets currently issued to them (and their own history); raise "report issue" and "return request" |

**Rules**
- Permissions are enforced on the server (API), never only in the interface.
- Roles are designed to be extensible (future: Auditor, Department Head).
- Every account is linked to an employee record (employee number, department, designation, location).

---

## 3. Asset categories and their data

All assets share a common record. Each category adds its own detail fields.

### 3.1 Common fields (all assets)
Asset ID (system generated, e.g. `AST-000123`), category, sub-category, name/description, status, condition, purchase date, purchase cost, supplier, invoice number, warranty end date, location, department, current value, QR code, photos, notes, created/updated timestamps and users.

### 3.2 Vehicles (cars, lorries, motorbikes)
Registration number, vehicle type, make, model, year, chassis number, engine number, fuel type, colour, odometer/mileage, insurance provider and expiry, revenue licence expiry, emission test expiry, next service date, documents (registration book, insurance).

### 3.3 IT equipment
- **Laptops / smartphones / mobile phones:** brand, model, serial number, IMEI (phones), specs (RAM, storage, OS), accessories issued, warranty.
- **Landlines:** number, handset model, extension, connection provider.
- **Printers / thermal printers:** brand, model, serial number, connection type, consumables note.
- **SIM cards:** SIM number (ICCID), mobile number, type (Data or Voice), network provider, plan, monthly limit, linked device (optional).

All IT equipment receives a QR code. QRs are generated for all other assets too, for consistency.

### 3.4 Fuel cards
Card provider, masked card number, card holder/assigned vehicle (optional), monthly limit, expiry date, status. PINs are never stored in the system.

---

## 4. Functional requirements

### 4.1 Asset registry
- Create, edit, view, search, filter and retire assets.
- Separate category forms (one per category).
- Bulk import from Excel/CSV for existing registers.
- Unique checks on serial number, IMEI, SIM number, registration number.
- Soft delete only (status changes to Disposed or Retired); history is kept.

### 4.2 Photos and documents
- Upload multiple photos per asset from web or mobile camera.
- Upload documents (invoice, warranty card, vehicle papers).
- Automatic thumbnail generation; file type and size validation.

### 4.3 Assignment and custody, including previous users
- Issue an asset to an employee; record issue date, issuing admin, condition at issue, accessories, acknowledgment.
- Transfer between employees; return with condition at return and receiving admin.
- **Full history of previous users:** every assignment is stored permanently. Each record keeps the employee link **and a snapshot of their details at that time** (name, employee number, department, designation, location, phone, email), so history remains correct even if the employee later changes department or leaves.
- Only one active assignment per asset (enforced by a database constraint).
- Employee records are deactivated, never deleted.
- Screens: "Current holder", "Previous holders" timeline on each asset; "Assets held now" and "Assets held previously" on each employee.

### 4.4 Condition monitoring
- Condition scale: New, Good, Fair, Poor, Damaged.
- Status (kept separate from condition): In stock, Assigned, Under repair, Lost, Disposed.
- Condition log entries (date, condition, notes, photo, recorded by).
- Users can report an issue; admins review and update condition.

### 4.5 Valuation and depreciation
- Purchase value fixed at registration.
- Current value from a depreciation rule per category (straight-line by default; reducing balance optional). Rules confirmed with finance.
- A scheduled monthly job writes a valuation record for every active asset.
- Manual revaluation by admin/super admin with a mandatory note.
- Value history chart per asset.

### 4.6 Maintenance and expiry
- Maintenance/service records (date, type, cost, vendor, notes).
- Alerts for warranty end, vehicle insurance/licence/emission expiry, service due, fuel card expiry.
- Notification by in-app alert and email.

### 4.7 QR service
- Generate a QR per asset encoding a URL (`https://<host>/a/<asset-id>`), so the QR never needs reprinting when details change.
- Bulk label sheet (PDF) and single label printing.
- Scan from mobile camera or USB scanner to open asset, assign, return or log condition.
- Stock-take mode: scan assets in a location; system lists missing and unexpected assets.

### 4.8 Dashboards
- **Company dashboard (Admin/Super Admin):** total assets; count per category and sub-category; assigned / in stock / under repair / disposed; total purchase value vs current value; expiring items; recent activity.
- **User dashboard:** cards for each assigned asset with photo, condition, QR and issue date; history tab; report-issue action.

### 4.9 Reports
1. Category-wise asset report.
2. Consumer-wise (employee/department) assignment report.
3. Asset lifetime report: purchase, every assignment, maintenance, condition changes, valuation trend, disposal.
4. Previous users report for a given asset.
5. Unassigned/in-stock assets.
6. Expiry and warranty report.
7. Depreciation summary (finance).
8. Lost/damaged/disposed assets.
9. SIM and fuel card report.
10. Employee clearance report (all assets an employee must return).
11. Audit log report.

Filters: date range, category, department, location, status. Export to PDF and Excel.

### 4.10 Audit trail
Every create, update, assign, return, revalue, approve and delete action is logged (who, what, when, old and new values).

### 4.11 Approvals
Disposal and write-off requests require Super Admin approval.

### 4.12 Dispatch forms and form templates
- A **dispatch form** is the paper or digital record signed when an asset is handed over (issued, transferred or sent to another location).
- **Download:** from an assignment or dispatch, an admin downloads the form pre-filled with employee details, asset details, accessories, condition, date, issuing admin and a unique form number.
- **Upload:** the completed and signed copy (PDF, JPG/PNG scan or phone photo, or Word/Excel) is uploaded and linked to that assignment. It appears in the asset's history and the employee's record.
- **Form status:** Generated, Awaiting signed copy, Signed copy uploaded, Verified. Admins can list all assignments still awaiting a signed copy.
- **Changeable structure:** the form layout is not hard-coded. Admins upload a template file (Word `.docx`, Excel `.xlsx` or PDF) containing placeholders such as `{{employee_name}}` and `{{asset_id}}`. On upload the system validates the placeholders and reports unknown ones.
- **Versioning:** a new upload creates a new template version. Old versions are kept, because earlier forms were generated from them. Only one version per form type is active at a time.
- **Supported behaviour by format:**
  - Word and Excel templates: filled automatically with placeholders.
  - PDF templates: filled automatically only if the PDF has form fields (AcroForm). A flat PDF without fields can be downloaded blank and printed, but cannot be auto-filled.
- **Permissions:** Super Admin activates templates and can view all forms. Admin uploads template drafts, generates forms and uploads signed copies. User can view and download their own signed forms.
- Uploaded files are validated (type, size), stored outside public folders and served only through a permission-checked endpoint.

**Standard placeholders:** `form_number`, `date`, `company_name`, `employee_name`, `employee_number`, `department`, `designation`, `location`, `phone`, `asset_id`, `asset_name`, `category`, `brand`, `model`, `serial_number`, `imei`, `registration_number`, `sim_number`, `mobile_number`, `condition`, `accessories`, `issued_by`, `remarks`.

---

## 5. Data model (PostgreSQL)

### 5.1 Core tables
- `users` (login, role, link to employee, is_active)
- `employees` (employee number, name, department, designation, location, phone, email, is_active)
- `departments`, `locations`
- `categories`, `subcategories`
- `assets` (shared fields, see 3.1)
- `vehicle_details`, `it_device_details`, `sim_details`, `fuel_card_details` (one-to-one with `assets`)
- `asset_media` (photos and documents)
- `assignments` (see 5.2)
- `condition_logs`
- `valuation_records`, `depreciation_rules`
- `maintenance_records`
- `approval_requests`
- `form_templates` (form type, name, version, file, file type, placeholders found, is_active, uploaded_by, activated_by, notes)
- `dispatch_forms` (form number, assignment, template version used, generated file, signed file, status, generated_by, uploaded_by, uploaded_at, verified_by, remarks)
- `notifications`
- `audit_logs`

### 5.2 `assignments` (asset custody history)
| Field | Notes |
|---|---|
| asset | FK to assets |
| employee | FK to employees (never deleted) |
| employee_name, employee_number, department_name, designation, location_name, phone, email | **Snapshot at issue time** |
| issued_at, issued_by | |
| condition_at_issue, accessories_issued, issue_notes | |
| acknowledged_at | employee acknowledgment |
| returned_at, received_by | null while active |
| condition_at_return, return_notes | |
| status | Active / Returned / Transferred |

**Constraint:** a partial unique index allows only one row per asset where `returned_at IS NULL`.

### 5.3 Data rules
- History tables (assignments, condition logs, valuation records, maintenance, audit) are append-only.
- No hard deletes of assets, employees or history.
- Sensitive fields (fuel card numbers) masked in the interface and encrypted at rest where practical.
- Index on foreign keys, status, category, serial number, registration number, IMEI.

---

## 6. Architecture

```
            Web (React)      Mobile (Expo)      Desktop (PyWebView)
                 \                |                   /
                  \               |                  /
                   +---- REST API (Django REST Framework, JWT) ----+
                                     |
                +--------------------+--------------------+
                |                    |                    |
           PostgreSQL        File storage (media)   Redis + Celery
                                                   (scheduled jobs)
```

One central server and one shared database. All clients use the same API, so business rules exist in one place only.

### 6.1 Technology choices
| Layer | Choice |
|---|---|
| Database | PostgreSQL |
| Backend | Python, Django, Django REST Framework |
| Auth | JWT (SimpleJWT), role-based permissions |
| API docs | OpenAPI/Swagger via drf-spectacular |
| Web | React (Vite) + Tailwind CSS |
| Mobile | React Native with Expo (camera, QR scanner) |
| Desktop | PyWebView wrapping the web app |
| File storage | Local server storage first; S3-compatible storage (MinIO/S3) later |
| Background jobs | Celery + Redis |
| QR | `segno` or `qrcode` |
| Reports | WeasyPrint or ReportLab (PDF), openpyxl (Excel) |
| Images | Pillow |
| Form templates | `docxtpl` (Word), `openpyxl` (Excel), `pypdf` (fillable PDF fields) |
| Deployment | Linux, Nginx, Gunicorn, Docker |
| Monitoring | Sentry, daily automated database backups |

### 6.2 Backend modules (one Django app each)
`accounts`, `employees`, `assets`, `vehicles`, `itdevices`, `sims`, `fuelcards`, `assignments`, `valuation`, `maintenance`, `media`, `qrcodes`, `reports`, `dashboard`, `notifications`, `approvals`, `audit`, `dispatch` (templates and forms).

Each app contains the same small files: `models.py`, `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `tests.py`, so any service can be updated independently.

### 6.3 Repository layout
```
hoplon/
├── docs/
├── backend/
│   ├── config/
│   ├── accounts/ employees/ assets/ vehicles/ itdevices/ sims/ fuelcards/
│   ├── assignments/ valuation/ maintenance/ media/ qrcodes/
│   ├── reports/ dashboard/ notifications/ approvals/ audit/
│   ├── manage.py
│   └── requirements.txt
├── web/src/pages/        one file per screen
├── mobile/src/screens/   one file per screen
└── desktop/
```

---

## 7. API outline (REST, prefix `/api/v1/`)

| Area | Endpoints (examples) |
|---|---|
| Auth | `POST auth/login`, `POST auth/refresh`, `GET auth/me` |
| Employees | `GET/POST employees`, `GET/PATCH employees/{id}`, `GET employees/{id}/assets` |
| Assets | `GET/POST assets`, `GET/PATCH assets/{id}`, `GET assets/by-qr/{code}` |
| Category details | `vehicles`, `it-devices`, `sims`, `fuel-cards` (nested with assets) |
| Media | `POST assets/{id}/media`, `GET assets/{id}/media` |
| Assignments | `POST assets/{id}/assign`, `POST assets/{id}/return`, `POST assets/{id}/transfer`, `GET assets/{id}/assignments` (previous users) |
| Condition | `GET/POST assets/{id}/condition-logs` |
| Valuation | `GET assets/{id}/valuations`, `POST assets/{id}/revalue` |
| Maintenance | `GET/POST assets/{id}/maintenance` |
| QR | `GET assets/{id}/qr`, `POST qr/labels` |
| Dashboard | `GET dashboard/summary`, `GET dashboard/my-assets` |
| Reports | `GET reports/category`, `reports/consumer`, `reports/lifetime/{id}`, with `?format=pdf|xlsx` |
| Form templates | `GET/POST form-templates`, `POST form-templates/{id}/activate`, `GET form-templates/{id}/download` |
| Dispatch forms | `POST assignments/{id}/dispatch-form` (generate), `GET dispatch-forms/{id}/download`, `POST dispatch-forms/{id}/upload-signed`, `GET dispatch-forms?status=awaiting` |
| Approvals | `POST approvals`, `POST approvals/{id}/decide` |
| Audit | `GET audit` |

---

## 8. Screens

**All roles:** Login; My Assets dashboard; Asset detail (including previous holders); Report an issue; Return request.

**Admin and Super Admin:** Company dashboard; Asset list with filters; Add/edit asset (one form per category); Assign / transfer / return; Employees; QR labels; Condition log; Maintenance; Reports; Alerts; Bulk import; Dispatch forms (generate, download, upload signed copy, pending list).

**Super Admin only:** Form templates (upload, preview placeholders, activate, version history); Admin management; Approvals; Audit log; Depreciation rules; System settings.

**Mobile app:** Login; scan QR; add new asset with camera; asset detail; assign/return; my assets; report issue.

---

## 9. Non-functional requirements

- **Security:** HTTPS, hashed passwords, login rate limiting, optional MFA, server-side permission checks, upload validation, secrets in environment variables.
- **Performance:** pagination, database indexes, thumbnails, cached dashboard summaries.
- **Reliability:** daily backups with tested restores.
- **Auditability:** complete change log.
- **Usability:** simple user dashboard, responsive layout, consistent forms.
- **Localisation:** LKR currency; date formats; later Sinhala/Tamil labels.
- **Maintainability:** modular apps, API documentation, automated tests per module.

---

## 10. Development roadmap (sequential tasks)

| # | Task | Output |
|---|---|---|
| 1 | Project skeleton (done) | Folder layout, Django config, PostgreSQL connection, environment settings |
| 2 | Accounts and roles (done) | Custom user model, three roles, JWT login, permissions |
| 3 | Employees (done) | Employee, department, location models and API |
| 4 | Assets | Shared asset table, categories, auto asset IDs |
| 5 | Category details | Vehicles, IT devices, SIMs, fuel cards |
| 6 | Media | Photo and document upload |
| 7 | Assignments | Issue, transfer, return, previous-users history |
| 8 | Dispatch forms and templates | Template upload and versions, form generation (Word/Excel/PDF), signed copy upload |
| 9 | QR codes | Generation, lookup, label sheets |
| 10 | Condition and valuation | Logs, depreciation, scheduled job |
| 11 | Dashboard API | Counts and summaries |
| 12 | Maintenance, alerts, approvals, audit | |
| 13 | Reports | Category, consumer, lifetime, exports |
| 14 | Web frontend | Screen by screen |
| 15 | Mobile app | Screen by screen |
| 16 | Desktop wrapper, import tool, deployment | |

Each task is delivered as a small set of files with exact paths and a commit message, and is tested before the next begins.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Existing asset data is messy | Bulk import tool with validation report |
| Depreciation rules disagree with finance | Agree rules with finance before Task 9; make rules configurable |
| Employees leave, history breaks | Snapshot fields in assignments; deactivate, never delete |
| Sensitive card data exposure | Mask, encrypt, never store PINs |
| Scope growth | Follow the task roadmap; log new ideas in a backlog |
| Data loss | Automated backups, tested restores |

---

## 12. Glossary

- **Asset:** any physical item the company owns and issues.
- **Assignment:** the period an asset is held by one employee.
- **Consumer:** the employee (or department) holding an asset.
- **Book value / current value:** asset value after depreciation.
- **QR label:** printed code linking to the asset's page.
