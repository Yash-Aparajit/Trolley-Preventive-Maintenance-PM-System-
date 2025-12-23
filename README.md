# 🚛 Trolley Preventive Maintenance (PM) System

![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Status](https://img.shields.io/badge/Status-Live%20Demo-success)

A **Streamlit-based Preventive Maintenance (PM) application** for managing
maintenance, damage reporting, repair costs, reminders, and lifecycle tracking
of material handling trolleys in a manufacturing plant.

This system is designed to **replace manual Excel sheets**, improve PM discipline,
reduce downtime, track repeated failures, and maintain a **digital maintenance
history for every trolley**.

---

## 🚀 Live Demo

🔗 **Streamlit App:**  
https://trolley-maintenance.streamlit.app/

⚠️ **Demo Notice:**  
This is a public demo deployment using **temporary sample data**.  
Data may reset on app restart, redeploy, or inactivity (Streamlit Cloud behavior).

---

## ▶️ Try It Yourself

1. Open the live demo link above
2. Register a few trolley IDs
3. Log preventive maintenance or report a damage
4. Check reminders, history, and cost dashboards
5. Export records to Excel

No login required.

---

## 🧰 Tech Stack

- **Python 3.10+**
- **Streamlit** – Frontend UI
- **SQLite** – Local file-based database (`pm_demo.db`)
- **Pandas** – Data handling, filtering, reporting
- **openpyxl** – Excel (XLSX) export engine
- **Python Standard Library** – `datetime`, `os`, `shutil`, `io`, `re`

---

## ✨ Key Features

### 🏠 Dashboard
- Displays:
  - Total trolleys maintained
  - Overdue PM count
  - Upcoming PM (next 7 days)
  - Recent damage reports
  - Scrapped trolleys
  - Total maintenance cost (Week / Month / Year)

---

### 🛠 Log Preventive Maintenance
- Record routine PM activity
- Auto-calculates next PM date (default +90 days)
- Optionally store:
  - Technician name  
  - Maintenance cost (₹)
  - Notes

---

### ⚠ Report Damage / Failures
- Log damages with categories:
  - `HANDLE_BREAK`
  - `WHEEL_ISSUE`
  - `FRAME_BEND`
  - `OTHER`
- Store detailed notes, technician name, and repair cost
- Automatically creates PM entries
- Tracks repeated failures and raises alerts after **3+ occurrences**

---

### 🔍 Trolley Lookup (Full Lifecycle View)
- View complete trolley history:
  - All PM and failure records
  - Cumulative cost
  - Risk assessment (Low / Medium / High)
  - Scrap status (if applicable)

---

### 🔔 PM Reminders
- Shows:
  - Overdue PMs
  - Upcoming PMs (next 7 days)
- Allows **Mark Done** directly from reminder screen

---

### 📝 History & Exports
- Filter records by:
  - Trolley ID
  - Year
  - Month
- Separate tabs for:
  - Maintenance
  - Failures
  - Registry (ID mapping)
  - Scrapped trolleys
- Export data to:
  - CSV
  - Excel (XLSX)

---

### ➕ Trolley ID Management
- Register new trolley IDs
- Modify / remap existing trolley IDs
- Maintain traceability for ID changes with notes

---

### 🗑 Scrap Trolley
- Mark trolleys as scrapped
- Record:
  - Scrap date
  - Reason
  - Recorded by

---

### 💾 Backup & Restore Database
- Download current SQLite database file (`pm_demo.db`)
- Restore system from an uploaded `.db` backup
- Useful for:
  - Manual backups
  - Shifting system between machines

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
