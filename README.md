# CampusLib Pro • TQM Library & Staff Management System
**Total Quality Management (TQM) Project Architecture Guide**

---

## 📂 Project Directory Structure & Responsibility Map

This application is built with a **Clean Modular Architecture** adhering to Total Quality Management (TQM) principles:

```text
Library Management System/
│
├── 📂 app/                              # Core Application Package
│   ├── __init__.py                      # Package descriptor and versioning
│   ├── config.py                        # Centralized settings, SLA targets & TQM parameters
│   │
│   ├── 📂 core/                         # Enterprise Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── logger.py                    # Rotating file audit logger (TQM Quality Monitoring)
│   │   └── security.py                  # Bcrypt salted password security (TQM Error Prevention)
│   │
│   ├── 📂 models/                       # SQLAlchemy Relational ORM Layer
│   │   ├── __init__.py                  # Model exports
│   │   ├── base.py                      # DeclarativeBase, SQLite WAL mode, PRAGMA foreign keys
│   │   ├── user.py                      # Staff user entity & role-based permissions
│   │   ├── member.py                    # Student/patron directory with borrow quota validation
│   │   ├── book.py                      # Textbook catalog, copy constraints & defect flags
│   │   ├── loan.py                      # Circulation loans with automated overdue & fine rules
│   │   ├── payroll.py                   # Staff shifts & automated payroll calculation engine
│   │   └── quality_log.py               # TQM Quality Monitoring & continuous improvement ledger
│   │
│   ├── 📂 services/                     # Business Logic & Automation Engines
│   │   ├── __init__.py
│   │   ├── db_service.py                # Schema initialization & sample data seeder
│   │   ├── circulation_service.py       # Book issue, return & fine settlement logic
│   │   ├── payroll_service.py           # Shift aggregation & salary calculation
│   │   ├── analytics_service.py         # Pandas TQM statistical metrics & KPI aggregations
│   │   └── report_service.py            # ReportLab PDF slips & OpenPyXL Excel export
│   │
│   └── 📂 ui/                           # PySide6 Modern Desktop GUI Layer
│       ├── __init__.py
│       ├── styles.py                    # Executive Slate QSS design stylesheet
│       ├── 📂 components/               # Custom StatCards, SearchInputs, KPI Badges
│       └── 📂 views/                    # Distinct functional views
│           ├── login_view.py            # Authentication with bcrypt verification
│           ├── dashboard_view.py        # Real-time metrics & embedded Matplotlib charts
│           ├── books_view.py            # Catalog view with multi-criteria fast search & filter
│           ├── circulation_view.py      # Circulation desk with automatic overdue detection
│           ├── payroll_view.py          # Staff shift management & 1-click automated payroll
│           └── quality_audit_view.py    # TQM Quality Monitoring log & SLA defect tracker
│
├── 📂 data/                             # SQLite Persistent Storage
│   └── campus_tqm.db                    # Database with WAL journal mode
│
├── 📂 logs/                             # System Audit Trail
│   └── tqm_system.log                   # Rotating 5MB log file for quality audits
│
├── 📂 reports/                          # Generated Documents
│   ├── (PDF Pay Slips & Quality Summaries)
│   └── (Excel Audits & Catalog Reports)
│
├── 📄 test_part1.py                     # Single-command verification script for Core & Security
├── 📄 test_part2.py                     # Single-command verification script for Database & Models
├── 📄 run.py                            # Main application launcher
└── 📄 requirements.txt                  # Production dependencies
```

---

## 🎯 How Each Folder Maps to Your College TQM Viva Objectives

| Folder / Module | Primary TQM Objective | Practical Real-World Implementation |
| :--- | :--- | :--- |
| [`app/config.py`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/config.py) | **Standardization** | Centralizes loan durations (14 days), fine rates (₹5/day), and overtime multipliers (1.5x) so formulas are never hardcoded. |
| [`app/core/security.py`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/core/security.py) | **Error Prevention** | Enforces bcrypt salted password hashing, eliminating cleartext password vulnerabilities. |
| [`app/core/logger.py`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/core/logger.py) | **Quality Monitoring** | Automatically records all operations and errors to a 5MB rotating file [`logs/tqm_system.log`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/logs/tqm_system.log). |
| [`app/models/`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/models/) | **Data Accuracy & Consistency** | Relational foreign keys, unique ISBN/USN indexes, and SQL check constraints (`available_copies >= 0`). |
| [`app/models/payroll.py`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/models/payroll.py) | **Process Automation** | Automatically aggregates shift hours and calculates regular pay, overtime bonus, tax deductions, and net salary. |
| [`app/models/quality_log.py`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/models/quality_log.py) | **Continuous Improvement** | Measures millisecond execution time of database queries and tracks defect resolutions. |
| [`app/ui/views/`](file:///c:/Users/Dell/OneDrive/Dokumen/Library%20Managemet%20System/app/ui/views/) | **Customer Focus & Usability** | PySide6 responsive UI with live search filters, dashboard KPI cards, and instant error dialogs. |

---

## ⚡ How to Run Verifications

Run these commands in PowerShell or Command Prompt:

# Verify Part 1 (Config, Logger & Bcrypt)
.\.venv\Scripts\python.exe test_part1.py

# Verify Part 2 (Database ORM & Sample Data)
.\.venv\Scripts\python.exe test_part2.py

# Verify Part 3 (Services & Business Logic)
.\.venv\Scripts\python.exe test_part3.py

# Verify Part 4 (Reports & Document Export)
.\.venv\Scripts\python.exe test_part4.py

# Launch Full Desktop GUI Application
.\.venv\Scripts\python.exe run.py
```

### 🔑 Default Staff Credentials for Viva / Demo:
- **Chief Librarian (Admin):** `admin` / `admin123`
- **Circulation Officer:** `priya_desk` / `priya123`
- **Catalog Specialist:** `rahul_catalog` / `rahul123`