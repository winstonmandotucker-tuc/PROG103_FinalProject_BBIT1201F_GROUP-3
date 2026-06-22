# EcoClean SL — Smart Waste Management & Collection Tracking System

A desktop GUI application built in Python (tkinter) for managing household and community waste collection requests in Sierra Leone. Built as the Final Project for **PROG103: Principles of Structured Programming** at Limkokwing University of Creative Technology, Sierra Leone.

> Aligned with **UN Sustainable Development Goal 11: Sustainable Cities and Communities**, with secondary relevance to SDG 3 (Good Health and Well-Being) and SDG 12 (Responsible Consumption and Production).

---

## 📌 Problem It Solves

Many communities in Sierra Leone have no formal channel to request waste collection, and sanitation teams have no centralised way to track requests, prioritise urgent cases, or measure performance. EcoClean SL gives residents (via staff) a simple registration form, gives field supervisors a filterable collection queue, and gives management a reporting and audit-trail tool — turning an informal, undocumented process into a structured, accountable one.

## ✨ Features

- **Role-based access control** — Administrator, Supervisor, and Operator accounts each see a different sidebar and a different set of pages.
- **Register Request** — input module for new waste collection requests, with validation on phone number and quantity.
- **Collection Queue** — filterable by status and priority, with click-to-sort columns and colour-coded rows (overdue, urgent, completed, pending).
- **Search Records** — search by request ID, resident name, phone number, or community.
- **Update Status** — move a request through Pending → Assigned → Collected → Completed, with collector/team assignment.
- **Dashboard** — live KPI cards (total, pending, completed, urgent, overdue, total KG collected), recent activity feed, community statistics, and a waste-type breakdown chart.
- **Reports** — generate, view, and export a daily summary report (.txt) and full record export (.csv).
- **Activity Log** *(Administrator only)* — a full audit trail of every action taken in the system and who performed it.
- **Persistent storage** — all data is saved locally to `data.json` using an atomic write (write-then-replace) so the file can't be left corrupted by an interrupted save.

## 🖥️ Tech Stack

- **Language:** Python 3
- **GUI:** tkinter / ttk (standard library — no external GUI dependencies)
- **Data storage:** JSON (local file, `data.json`)
- **Export formats:** CSV, plain text

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or later (tkinter ships with most standard Python installations)

### Installation & Run

```bash
# Clone the repository
git clone https://github.com/<your-username>/ecoclean-sl.git
cd ecoclean-sl

# Run the application
python3 ecoclean_sl.py
```

No external packages are required — the project uses only Python's standard library (`tkinter`, `json`, `csv`, `os`, `datetime`).

### Demo Accounts

| Role          | Username     | Password    | Access                                  |
|---------------|--------------|-------------|------------------------------------------|
| Administrator | `admin`      | `admin123`  | Full access, including Activity Log      |
| Supervisor    | `supervisor` | `eco2026`   | All pages except Activity Log            |
| Operator      | `operator`   | `waste123`  | Dashboard, Register, Queue, Search, Status only |

## 📂 Project Structure

```
ecoclean-sl/
├── ecoclean_sl.py        # Main application (single-file)
├── data.json              # Auto-generated on first save (not tracked in git)
├── README.md
├── LICENSE
└── docs/
    └── screenshots/        # System & source code screenshots
```

## 🧱 Structured Programming Principles Applied

- **Variables & constants** for configuration (`APP_TITLE`, `OVERDUE_DAYS`, `WASTE_TYPES`, etc.)
- **Multiple data types** — strings, floats, integers, booleans, lists, and dictionaries
- **Decision structures** (`if` / `elif` / `else`) for validation and status logic
- **Iteration** (`for` loops) for searching, filtering, totalling, and populating tables
- **30+ user-defined functions/methods**, with backend logic fully separated from the GUI layer

## 🔐 Data, Privacy & Compliance

- Only the minimum personal data needed (name, phone, community) is collected.
- Data is stored locally in a human-readable, exportable format (JSON → CSV/TXT), avoiding lock-in to any proprietary format.
- The Activity Log tracks staff actions for accountability, not resident behaviour.

## 📄 License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.

## 🎓 Academic Context

- **Module:** PROG103 — Principles of Structured Programming
- **Institution:** Limkokwing University of Creative Technology, Sierra Leone
- **Examiner:** Elijah Fullah
- **Semester:** 02, March 2026 – July 2026
