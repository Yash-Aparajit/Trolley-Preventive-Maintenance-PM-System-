# Trolley Preventive Maintenance (PM) System  
A Streamlit-based application for managing Preventive Maintenance (PM), damage reporting, repair costs, PM reminders, trolley lifecycle, and maintenance dashboards inside a manufacturing plant.

This system is designed to replace manual Excel sheets, ensure transparency, reduce PM delays, track repeated failures, and maintain a digital maintenance history for every plant trolley.

---

## 🧰 Tech Stack
- **Python 3.10+**
- **Streamlit** – Frontend UI
- **SQLite** – Local database (`pm_demo.db`)
- **Pandas** – Data handling & exports
- **openpyxl** – Excel export
- **Datetime, os, shutil** – Python standard modules

---

## ✨ Key Features

### 🏠 Dashboard
- Displays:
  - Total trolleys maintained
  - Overdue PM count
  - Upcoming PM (next 7 days)
  - Recent damages
  - Scrapped trolleys
  - Total maintenance cost (Week / Month / Year)

### 🛠 Log Preventive Maintenance
- Record routine PM activity
- Auto-calculates next PM date (default +90 days)
- Optionally store:
  - Technician name  
  - Cost (₹)
  - PM notes

### ⚠ Report Damage / Failures
- Log damages with category:
  - HANDLE_BREAK
  - WHEEL_ISSUE
  - FRAME_BEND
  - OTHER
- Store detailed notes, technician name, and repair cost
- Auto-creates PM entry along with failure
- Tracks repeated issues (alerts after 3+ occurrences)

### 🔍 Trolley Lookup (Full History)
- View complete lifecycle of a trolley:
  - All PM and failure records
  - Costs
  - Risk assessment
  - Scrap status (if applicable)

### 🔔 PM Reminders
- Shows overdue PMs  
- Shows upcoming PM for next 7 days  
- Allows “Mark Done” from inside the reminder screen

### 📝 History & Exports
- Filter by:
  - Trolley ID
  - Year
  - Month
- Tabs:
  - Maintenance
  - Failures
  - Registry (ID mapping)
  - Scrapped trolleys
- Export to:
  - CSV
  - Excel (XLSX)

### ➕ Trolley ID Management
- Register new trolley IDs  
- Modify/remap existing trolley IDs  
- Log reasons for ID changes  

### 🗑 Scrap Trolley
- Mark trolleys as scrapped
- Record:
  - Scrap date  
  - Reason  
  - Recorded by  

### 💾 Backup & Restore Database
- Download current SQLite DB file (`pm_demo.db`)
- Restore from an uploaded `.db` file
- Ideal for manual backup or shifting system to another PC

---
