"""
Trolley Preventive Maintenance (PM) Application
-----------------------------------------------

Author: YOUR_NAME_HERE
Created: 2025-11-24
Last Updated: 2025-11-24
License: Internal use (Plant Maintenance)

Overview
========
This Streamlit application is managing Preventive Maintenance (PM), damage
reporting, and lifecycle tracking for material handling trolleys in a plant.

The app is providing:
    - A dashboard that is showing:
        * how many trolleys are maintained,
        * how many are overdue for PM,
        * how many damage events are reported,
        * how many trolleys are scrapped,
        * and total maintenance cost.
    - A form that is logging regular PM activities (with or without damage).
    - A form that is reporting damage/failure with category, note, technician
      name and cost.
    - Registration and modification of trolley IDs (ADD / MODIFY).
    - Scrapping of trolleys when they are going beyond repair.
    - Reminder view for overdue and upcoming PM (next 7 days).
    - Per-trolley lookup that is showing history, risk level and cost.
    - History / Records view with filters and export to CSV / Excel.
    - Simple Backup & Restore for the SQLite database file.

Technology stack
================
    - Streamlit  : UI layer
    - SQLite     : Local file-based database (pm_demo.db)
    - Pandas     : Data manipulation and reporting
    - openpyxl   : Excel export engine (via pandas)
    - Python std : datetime, os, re, io, shutil

Database tables
===============
    - maintenance:
        * One row per PM or failure record.
        * Columns: id, trolley_id, pm_date, next_due, failure_type,
          failure_note, technician, amount, created_at.
    - alerts:
        * Tracking repeated failures for the same trolley and failure type.
        * Used for highlighting chronic issues.
    - trolley_registry:
        * Recording ADD / MODIFY actions when trolley IDs are created or
          remapped.
    - scrapped:
        * Tracking trolleys that are permanently scrapped.

How to run
==========
    streamlit run app.py

Notes
=====
    - The database file (pm_demo.db) is staying next to this script by default.
    - The Backup & Restore screen is allowing you to download and restore the
      .db file manually.
    - This file, along with your Git commits or email backups, is serving as
      proof of authorship and timestamp for this work.
"""

# ----------------------------
# This section is importing all required libraries
# ----------------------------
import streamlit as st
from datetime import datetime, timedelta, date
import sqlite3
import pandas as pd
import re
import os
import shutil
from io import BytesIO

# ----------------------------
# This section is configuring core constants
# ----------------------------
DB_PATH = "pm_demo.db"
PM_INTERVAL_DAYS = 90          # 3 months
ALERT_THRESHOLD = 3            # repeated failure count
SCREENSHOT_PATH = "/mnt/data/Screenshot 2025-11-24 100049.png"  # optional preview image

# This call is configuring the Streamlit page
st.set_page_config(page_title="Trolley PM", layout="wide")

# ----------------------------
# This section is defining language strings (English / Marathi)
# ----------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "en"   # default English


STRINGS = {
    "en": {
        "app_title": "Trolley Preventive Maintenance",
        "menu_title": "Menu",

        "btn_home": "Home",
        "btn_log": "Log Maintenance",
        "btn_report": "Report Damage",
        "btn_reminders": "Reminders",
        "btn_trolley": "Trolley Lookup",
        "btn_history": "Records & Exports",
        "btn_register": "Register New Trolley",
        "btn_modify": "Modify Trolley ID",
        "btn_scrap": "Scrap Trolley",
        "btn_backup": "Backup & Restore DB",
        "btn_back_home": "Back to Home",

        "page_log": "Log Maintenance",
        "page_report": "Report Damage",
        "page_scrap": "Scrap Trolley (Mark as scrapped)",
        "page_register": "Register New Trolley",
        "page_modify": "Modify / Remap Trolley ID",
        "page_reminders": "Reminders",
        "page_trolley": "Trolley Lookup",
        "page_history": "Records & Exports",
        "page_backup": "Backup & Restore Database",

        "home_dashboard": "Dashboard",
        "home_actions": "Actions",
        "home_records": "Records & Exports",
        "home_timeframe": "Timeframe:",
        "metric_maintained": "Trolleys maintained",
        "metric_overdue": "Trolleys overdue",
        "metric_damages": "Damages reported",
        "metric_scrapped": "Trolleys scrapped",
        "home_total_cost": "Total maintenance cost",
    },
    "mr": {
        "app_title": "ट्रॉली प्रिव्हेंटिव मेंटेनन्स",
        "menu_title": "मेनू",

        "btn_home": "होम",
        "btn_log": "मेंटेनन्स नोंदवा",
        "btn_report": "डॅमेज रिपोर्ट करा",
        "btn_reminders": "रिमाइंडर्स",
        "btn_trolley": "트्रॉली माहिती",
        "btn_history": "रेकॉर्ड्स आणि एक्सपोर्ट्स",
        "btn_register": "नवीन ट्रॉली नोंदणी",
        "btn_modify": "ट्रॉली आयडी बदला",
        "btn_scrap": "ट्रॉली स्क्रॅप करा",
        "btn_backup": "बॅकअप आणि रिस्टोर",
        "btn_back_home": "होमवर परत",

        "page_log": "मेंटेनन्स नोंदवा",
        "page_report": "डॅमेज रिपोर्ट",
        "page_scrap": "ट्रॉली स्क्रॅप (Scrap Trolley)",
        "page_register": "नवीन ट्रॉली नोंदणी",
        "page_modify": "ट्रॉली आयडी बदल",
        "page_reminders": "रिमाइंडर्स",
        "page_trolley": "ट्रॉली माहिती",
        "page_history": "रेकॉर्ड्स आणि एक्सपोर्ट्स",
        "page_backup": "डेटाबेस बॅकअप आणि रिस्टोर",

        "home_dashboard": "डॅशबोर्ड",
        "home_actions": "क्रिया (Actions)",
        "home_records": "रेकॉर्ड्स आणि एक्सपोर्ट्स",
        "home_timeframe": "टाइमफ्रेम:",
        "metric_maintained": "मेंटेनन्स केलेल्या ट्रॉली",
        "metric_overdue": "ओव्हरड्यू ट्रॉली",
        "metric_damages": "डॅमेज रिपोर्ट (संख्या)",
        "metric_scrapped": "स्क्रॅप केलेल्या ट्रॉली",
        "home_total_cost": "एकूण मेंटेनन्स खर्च",
    },
}


def get_lang() -> str:
    """
    This function is returning the currently selected language code.

    Returns:
        str: "en" or "mr".
    """
    return st.session_state.get("lang", "en")


def t(key: str) -> str:
    """
    This function is translating a key into the current language.

    Args:
        key (str): Translation key.

    Returns:
        str: Translated string if available; otherwise the key itself.
    """
    lang = get_lang()
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))


# ----------------------------
# This section is injecting the global CSS and pastel theming
# ----------------------------
st.markdown(
    r"""
<style>
/* This block is styling layout constraints and padding */
.block-container {
  max-width: 1000px;
  margin-left: auto;
  margin-right: auto;
  padding-top: 48px;
  padding-left: 18px;
  padding-right: 18px;
}

/* This block is styling the main app title */
.app-title {
  font-family: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  font-weight: 700;
  font-size: 26px;
  margin-bottom: 10px;
  color: #111827;
}

/* This block is styling background panels for different pages */
.page-bg-home {
  background: #f9fafb;
  padding: 12px 16px 20px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.page-bg-form {
  background: #f9fafb;
  padding: 12px 16px 20px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.page-bg-reminder {
  background: #f9fafb;
  padding: 12px 16px 20px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.page-bg-history {
  background: #f9fafb;
  padding: 12px 16px 20px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.page-bg-scrap {
  background: #fff7f7;
  padding: 12px 16px 20px 16px;
  border-radius: 12px;
  border: 1px solid #fecaca;
}

/* This block is styling big action buttons */
.big-btn .stButton>button {
  height:64px;
  width:100%;
  font-size:16px;
  border-radius:10px;
  border: 1px solid #e5e7eb;
  margin-top:4px;
}

/* These blocks are styling color themes for different action groups */
.btn-green .stButton>button {
  background: linear-gradient(180deg, #dcfce7 0%, #bbf7d0 100%) !important;
  color: #166534 !important;
}
.btn-orange .stButton>button {
  background: linear-gradient(180deg, #ffedd5 0%, #fed7aa 100%) !important;
  color: #7c2d12 !important;
}
.btn-blue .stButton>button {
  background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%) !important;
  color: #1e3a8a !important;
}
.btn-red .stButton>button {
  background: linear-gradient(180deg, #fee2e2 0%, #fecaca 100%) !important;
  color: #7f1d1d !important;
}

/* This block is adding hover effect on big buttons */
.big-btn .stButton>button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.16) !important;
}

/* This block is styling records area buttons */
.records-area .stButton>button {
  height:64px; width:100%; font-size:16px; border-radius:10px; margin-top:4px;
  background: linear-gradient(180deg,#eef7ff 0%,#e7f1ff 100%);
  border: 1px solid #d8eaff;
}

/* This block is styling the small red "back" buttons on the right */
.right-back .stButton>button {
  background:#fff0f0;
  color:#8b0000;
  border-radius:8px;
}

/* This block is making sidebar buttons compact */
[data-testid="stSidebar"] .stButton>button {
  margin:4px 0;
  padding:6px 8px;
  height:36px;
  font-size:14px;
  border-radius:6px;
}

/* This block is styling reminder items */
.reminder-overdue {
  background:#fff6f6;
  padding:10px;
  border-radius:6px;
  border-left:4px solid #ff8b8b;
  margin-bottom:6px;
}
.reminder-upcoming {
  background:#f6fff8;
  padding:10px;
  border-radius:6px;
  border-left:4px solid #5fd18b;
  margin-bottom:6px;
}

/* This block is styling generic form cards */
.form-card {
  background: #ffffff;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.10);
  margin-top: 6px;
}
.form-header {
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid #e5e7eb;
}

/* This block is making data table font a bit smaller */
.stDataFrame table {
  font-size:13px;
}
</style>
""",
    unsafe_allow_html=True,
)

# This block is rendering the main title
st.markdown(f'<div class="app-title">{t("app_title")}</div>', unsafe_allow_html=True)

# ----------------------------
# This section is initializing the database and handling migrations
# ----------------------------
@st.cache_resource
def get_db():
    """
    This function is creating (if needed) and returning a SQLite connection.

    It is:
        - Ensuring all required tables exist.
        - Ensuring optional columns (failure_type, failure_note,
          technician, amount) are present in the maintenance table.

    Returns:
        sqlite3.Connection: Open connection to the pm_demo.db database.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()

    # This query is creating the maintenance table if it is not existing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trolley_id TEXT NOT NULL,
            pm_date TEXT NOT NULL,
            next_due TEXT NOT NULL,
            failure_type TEXT,
            failure_note TEXT,
            technician TEXT,
            amount TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # This query is creating the alerts table if it is not existing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trolley_id TEXT NOT NULL,
            failure_type TEXT NOT NULL,
            occurrences INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        )
        """
    )

    # This query is creating the trolley_registry table if it is not existing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trolley_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_id TEXT,
            new_id TEXT,
            action TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # This query is creating the scrapped table if it is not existing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scrapped (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trolley_id TEXT NOT NULL,
            scrap_date TEXT NOT NULL,
            reason TEXT,
            recorded_by TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # This part is checking and adding missing optional columns in maintenance
    cur.execute("PRAGMA table_info(maintenance)")
    cols = [r[1] for r in cur.fetchall()]
    for col, coltype in {
        "failure_type": "TEXT",
        "failure_note": "TEXT",
        "technician": "TEXT",
        "amount": "TEXT",
    }.items():
        if col not in cols:
            cur.execute(f"ALTER TABLE maintenance ADD COLUMN {col} {coltype}")
    conn.commit()

    return conn


# This section is creating a shared DB cursor
conn = get_db()
cur = conn.cursor()

# ----------------------------
# This section is defining utility helpers
# ----------------------------
def iso(d: date) -> str:
    """
    This function is converting a date object into ISO string (YYYY-MM-DD).

    Args:
        d (date): Date object.

    Returns:
        str: ISO formatted date string.
    """
    return d.isoformat()


def from_iso(s: str) -> date:
    """
    This function is converting an ISO date / datetime string into a date.

    Args:
        s (str): Input string in ISO format.

    Returns:
        date: Parsed date object.
    """
    return datetime.fromisoformat(s).date()


def fmt_indian(iso_date: str) -> str:
    """
    This function is formatting an ISO date string into DD/MM/YYYY format.

    Args:
        iso_date (str): Date string in ISO format.

    Returns:
        str: Formatted date in Indian style or the original string if parsing fails.
    """
    try:
        return from_iso(iso_date).strftime("%d/%m/%Y")
    except Exception:
        return iso_date or ""


def parse_amount_text(x):
    """
    This function is safely parsing amount values from text.

    It is:
        - Accepting numbers, strings with commas, or "NA".
        - Returning float for valid numbers, otherwise None.

    Args:
        x (Any): Raw value from DB or input.

    Returns:
        float | None: Parsed numeric value or None.
    """
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.upper() == "NA":
        return None
    s_clean = s.replace(",", "")
    if re.match(r"^\d+(\.\d+)?$", s_clean):
        return float(s_clean)
    return None


def fmt_amount(x):
    """
    This function is formatting an amount value with the ₹ symbol.

    Args:
        x (Any): Raw value from DB or input.

    Returns:
        str: Pretty string like '₹1,234.50' or 'NA'.
    """
    v = parse_amount_text(x)
    return f"₹{v:,.2f}" if v is not None else "NA"


def sum_amount(series) -> float:
    """
    This function is summing a list/series of amount values.

    Args:
        series (Iterable[Any]): Iterable of raw amount values.

    Returns:
        float: Total of parsed numeric values.
    """
    total = 0.0
    for val in series:
        v = parse_amount_text(val)
        if v is not None:
            total += v
    return total


def register_trolley(old_id, new_id, action, note):
    """
    This function is recording a trolley registry action (ADD / MODIFY).

    Args:
        old_id (str | None): Existing trolley ID (for MODIFY).
        new_id (str | None): New trolley ID (for ADD or MODIFY).
        action (str): Action type ("ADD" or "MODIFY").
        note (str | None): Free-text note.
    """
    cur.execute(
        """
        INSERT INTO trolley_registry (old_id, new_id, action, note, created_at)
        VALUES (?,?,?,?,?)
        """,
        (old_id or None, new_id or None, action, note or None, datetime.now().isoformat()),
    )
    conn.commit()


def update_alerts_if_needed(trolley_id, failure_type):
    """
    This function is updating the alerts table when failures are repeating.

    It is:
        - Counting how many times a particular failure_type is happening for
          a trolley.
        - If count is crossing ALERT_THRESHOLD, it is inserting/updating an
          alert entry.

    Args:
        trolley_id (str): Trolley ID.
        failure_type (str): Failure type/category.
    """
    cur.execute(
        "SELECT COUNT(*) FROM maintenance WHERE trolley_id = ? AND failure_type = ?",
        (trolley_id, failure_type),
    )
    count = cur.fetchone()[0]
    if count >= ALERT_THRESHOLD:
        cur.execute(
            "SELECT id FROM alerts WHERE trolley_id = ? AND failure_type = ? AND acknowledged = 0",
            (trolley_id, failure_type),
        )
        row = cur.fetchone()
        if row:
            # This query is updating an existing alert
            cur.execute(
                "UPDATE alerts SET occurrences = ?, created_at = ? WHERE id = ?",
                (count, datetime.now().isoformat(), row[0]),
            )
        else:
            # This query is creating a new alert
            cur.execute(
                """
                INSERT INTO alerts (trolley_id, failure_type, occurrences, created_at, acknowledged)
                VALUES (?, ?, ?, ?, 0)
                """,
                (trolley_id, failure_type, count, datetime.now().isoformat()),
            )
        conn.commit()


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """
    This function is converting a DataFrame into an in-memory Excel file.

    Args:
        df (pd.DataFrame): Data to export.

    Returns:
        bytes: Excel file content as bytes.
    """
    with BytesIO() as b:
        with pd.ExcelWriter(b, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        return b.getvalue()


# ----------------------------
# This section is managing navigation state and sidebar
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# This block is rendering the language toggle in sidebar
lang_choice = st.sidebar.radio(
    "Language / भाषा",
    options=("English", "मराठी"),
    index=0 if get_lang() == "en" else 1,
)
st.session_state.lang = "en" if lang_choice == "English" else "mr"

# This block is rendering the navigation menu in sidebar
st.sidebar.markdown(f"### {t('menu_title')}")
st.sidebar.button(f"🏠 {t('btn_home')}", on_click=lambda: st.session_state.update({"page": "home"}))
st.sidebar.button(f"🛠 {t('btn_log')}", on_click=lambda: st.session_state.update({"page": "log"}))
st.sidebar.button(f"⚠ {t('btn_report')}", on_click=lambda: st.session_state.update({"page": "report"}))
st.sidebar.button(f"🔔 {t('btn_reminders')}", on_click=lambda: st.session_state.update({"page": "reminders"}))
st.sidebar.button(f"🔍 {t('btn_trolley')}", on_click=lambda: st.session_state.update({"page": "trolley"}))
st.sidebar.button(f"📜 {t('btn_history')}", on_click=lambda: st.session_state.update({"page": "history"}))
st.sidebar.markdown("---")
st.sidebar.button(f"➕ {t('btn_register')}", on_click=lambda: st.session_state.update({"page": "register"}))
st.sidebar.button(f"🔁 {t('btn_modify')}", on_click=lambda: st.session_state.update({"page": "modify"}))
st.sidebar.button(f"🗑 {t('btn_scrap')}", on_click=lambda: st.session_state.update({"page": "scrap"}))
st.sidebar.markdown("---")
st.sidebar.button(f"💾 {t('btn_backup')}", on_click=lambda: st.session_state.update({"page": "backup_restore"}))
st.sidebar.button(f"🔙 {t('btn_back_home')}", on_click=lambda: st.session_state.update({"page": "home"}))

# This block is optionally showing a reference screenshot in sidebar
if os.path.exists(SCREENSHOT_PATH):
    st.sidebar.markdown("---")
    try:
        st.sidebar.image(SCREENSHOT_PATH, use_column_width=True)
    except Exception:
        st.sidebar.markdown(f"Screenshot path: `{SCREENSHOT_PATH}`")

# ----------------------------
# This section is rendering the HOME dashboard
# ----------------------------
if st.session_state.page == "home":
    st.markdown('<div class="page-bg-home">', unsafe_allow_html=True)

    st.markdown(f"### {t('home_dashboard')}")
    timeframe = st.radio(t("home_timeframe"), ("Week", "Month", "Year"), horizontal=True)

    # This block is determining the time window for metrics
    today = date.today()
    if timeframe == "Week":
        start = today - timedelta(days=7)
    elif timeframe == "Month":
        start = date(today.year, today.month, 1)
    else:
        start = date(today.year, 1, 1)
    start_iso = iso(start)
    today_iso = iso(today)

    # This block is calculating key metrics
    cur.execute("SELECT COUNT(DISTINCT trolley_id) FROM maintenance WHERE pm_date >= ?", (start_iso,))
    trolleys_maintained = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT trolley_id) FROM maintenance WHERE next_due <= ?", (today_iso,))
    trolleys_overdue = cur.fetchone()[0] or 0

    cur.execute(
        "SELECT COUNT(*) FROM maintenance WHERE failure_type IS NOT NULL AND pm_date >= ?",
        (start_iso,),
    )
    damages_reported = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM scrapped WHERE scrap_date >= ?", (start_iso,))
    trolleys_scrapped = cur.fetchone()[0] or 0

    cur.execute("SELECT amount FROM maintenance WHERE pm_date >= ?", (start_iso,))
    cost_rows = [r[0] for r in cur.fetchall()]
    total_cost = sum_amount(cost_rows)

    # This block is showing metrics in four columns
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{t('metric_maintained')} ({timeframe})", trolleys_maintained)
    col2.metric(t("metric_overdue"), trolleys_overdue)
    col3.metric(f"{t('metric_damages')} ({timeframe})", damages_reported)
    col4.metric(f"{t('metric_scrapped')} ({timeframe})", trolleys_scrapped)

    st.markdown(
        f"<div style='font-size:18px;font-weight:600;margin-top:8px;'>"
        f"{t('home_total_cost')} ({timeframe}): {fmt_amount(total_cost)}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # This block is rendering big action buttons
    st.markdown(f"### {t('home_actions')}")
    colA, colB, colC = st.columns(3)
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)

    with colA:
        st.markdown('<div class="btn-green">', unsafe_allow_html=True)
        st.button(f"🛠 {t('btn_log')}", on_click=lambda: st.session_state.update({"page": "log"}))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-orange">', unsafe_allow_html=True)
        st.button(f"⚠ {t('btn_report')}", on_click=lambda: st.session_state.update({"page": "report"}))
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        st.button(f"🔔 {t('btn_reminders')}", on_click=lambda: st.session_state.update({"page": "reminders"}))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        st.button(f"🔍 {t('btn_trolley')}", on_click=lambda: st.session_state.update({"page": "trolley"}))
        st.markdown("</div>", unsafe_allow_html=True)

    with colC:
        st.markdown('<div class="btn-green">', unsafe_allow_html=True)
        st.button(f"➕ {t('btn_register')}", on_click=lambda: st.session_state.update({"page": "register"}))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        st.button(f"🗑 {t('btn_scrap')}", on_click=lambda: st.session_state.update({"page": "scrap"}))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # .big-btn

    # This block is linking to records & exports page
    st.markdown(f"### {t('home_records')}")
    st.markdown("<div class='records-area'>", unsafe_allow_html=True)
    if st.button(t("btn_history")):
        st.session_state.page = "history"
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close page-bg-home

# ----------------------------
# This section is rendering the LOG MAINTENANCE form
# ----------------------------
elif st.session_state.page == "log":
    st.markdown('<div class="page-bg-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_log")}</div>', unsafe_allow_html=True)

    # This block is taking basic maintenance inputs
    trolley_id = st.text_input("Trolley ID (e.g. TRL-001):").strip()
    pm_date = st.date_input("Maintenance date:", value=date.today())
    failure_type = st.selectbox(
        "Failure category:",
        options=["NA", "HANDLE_BREAK", "WHEEL_ISSUE", "FRAME_BEND", "OTHER"],
    )
    if failure_type == "OTHER":
        failure_note = st.text_input("Issue (short):")
    else:
        failure_note = st.text_input("Notes (optional):")

    st.caption("If there is no damage, keep failure category as 'NA'.")
    technician = st.text_input("Technician name (who is performing):", value="")
    amount_text = st.text_input("Amount (₹) (enter number or 'NA'):", value="NA")

    cols = st.columns([4, 1])
    with cols[0]:
        # This button is saving the maintenance record
        if st.button("Save"):
            if not trolley_id:
                st.error("Please provide a Trolley ID before saving.")
            else:
                ft = failure_type if failure_type != "NA" else None
                next_due = pm_date + timedelta(days=PM_INTERVAL_DAYS)
                cur.execute(
                    """
                    INSERT INTO maintenance
                        (trolley_id, pm_date, next_due, failure_type,
                         failure_note, technician, amount, created_at)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        trolley_id,
                        iso(pm_date),
                        iso(next_due),
                        ft,
                        failure_note or None,
                        technician or None,
                        amount_text or "NA",
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                st.success(
                    f"Saved for {trolley_id}. Next PM is due on "
                    f"{(pm_date + timedelta(days=PM_INTERVAL_DAYS)).strftime('%d/%m/%Y')}"
                )
                st.session_state.page = "home"
                st.rerun()
    with cols[1]:
        # This button is taking the user back to home
        st.markdown("<div class='right-back'>", unsafe_allow_html=True)
        if st.button(t("btn_back_home")):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)   # form-card
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-form

# ----------------------------
# This section is rendering the REPORT DAMAGE form
# ----------------------------
elif st.session_state.page == "report":
    st.markdown('<div class="page-bg-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_report")}</div>', unsafe_allow_html=True)

    trolley_id = st.text_input("Trolley ID (e.g. TRL-001):").strip()
    failure_date = st.date_input("Failure date:", value=date.today())
    failure_type = st.selectbox(
        "Failure type:",
        options=["HANDLE_BREAK", "WHEEL_ISSUE", "FRAME_BEND", "OTHER"],
    )
    if failure_type == "OTHER":
        failure_note = st.text_input("Issue (short):")
    else:
        failure_note = st.text_input("Notes (optional):")

    st.caption("Use this form when there is actual damage/failure.")
    technician = st.text_input("Technician name (who is reporting):", value="")
    amount_text = st.text_input("Repair amount (₹) (enter number or 'NA'):", value="NA")

    cols = st.columns([4, 1])
    with cols[0]:
        # This button is saving the damage report
        if st.button("Report"):
            if not trolley_id:
                st.error("Please provide Trolley ID before reporting.")
            else:
                cur.execute(
                    """
                    INSERT INTO maintenance
                        (trolley_id, pm_date, next_due, failure_type,
                         failure_note, technician, amount, created_at)
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        trolley_id,
                        iso(failure_date),
                        iso(failure_date + timedelta(days=PM_INTERVAL_DAYS)),
                        failure_type,
                        failure_note or None,
                        technician or None,
                        amount_text or "NA",
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                update_alerts_if_needed(trolley_id, failure_type)
                st.success(f"Reported {failure_type} for {trolley_id}")
                st.session_state.page = "home"
                st.rerun()
    with cols[1]:
        # This button is taking the user back to home
        st.markdown("<div class='right-back'>", unsafe_allow_html=True)
        if st.button(t("btn_back_home")):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)   # form-card
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-form

# ----------------------------
# This section is rendering the SCRAP TROLLEY form
# ----------------------------
elif st.session_state.page == "scrap":
    st.markdown('<div class="page-bg-scrap">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_scrap")}</div>', unsafe_allow_html=True)

    trolley_id = st.text_input("Trolley ID to scrap:").strip()
    scrap_date = st.date_input("Scrap date:", value=date.today())
    reason = st.text_input("Reason for scrapping (short):")
    recorded_by = st.text_input("Recorded by (name):", value="")
    st.caption("Scrap only when trolley is beyond repair or permanently not in use.")

    cols = st.columns([4, 1])
    with cols[0]:
        # This button is marking a trolley as scrapped
        if st.button("Mark Scrapped"):
            if not trolley_id:
                st.error("Enter trolley ID")
            else:
                cur.execute(
                    """
                    INSERT INTO scrapped (trolley_id, scrap_date, reason, recorded_by, created_at)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        trolley_id,
                        iso(scrap_date),
                        reason or None,
                        recorded_by or None,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                st.success(f"{trolley_id} is marked as scrapped")
                st.session_state.page = "home"
                st.rerun()
    with cols[1]:
        # This button is taking the user back to home
        st.markdown("<div class='right-back'>", unsafe_allow_html=True)
        if st.button(t("btn_back_home")):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)   # form-card
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-scrap

# ----------------------------
# This section is rendering the MODIFY / REMAP TROLLEY ID form
# ----------------------------
elif st.session_state.page == "modify":
    st.markdown('<div class="page-bg-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_modify")}</div>', unsafe_allow_html=True)

    old_id = st.text_input("Old trolley ID (existing):", key="mod_old")
    mapped_new = st.text_input("New trolley ID to map to (unique):", key="mod_new")
    mod_note = st.text_input("Reason / note for modification:", key="mod_note")
    st.caption("Use when a trolley is getting repurposed / renumbered to a new ID.")

    cols = st.columns([4, 1])
    with cols[0]:
        # This button is saving the modification mapping
        if st.button("Save modification mapping"):
            if not old_id.strip() or not mapped_new.strip():
                st.error("Both old and new IDs are required for modification.")
            else:
                register_trolley(
                    old_id.strip(), mapped_new.strip(), "MODIFY", mod_note.strip() or None
                )
                st.success(f"Recorded modification: {old_id.strip()} → {mapped_new.strip()}")
                st.session_state.page = "home"
                st.rerun()
    with cols[1]:
        # This button is taking the user back to home
        st.markdown("<div class='right-back'>", unsafe_allow_html=True)
        if st.button(t("btn_back_home")):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)   # form-card
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-form

# ----------------------------
# This section is rendering the REMINDERS screen
# ----------------------------
elif st.session_state.page == "reminders":
    st.markdown('<div class="page-bg-reminder">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_reminders")}</div>', unsafe_allow_html=True)

    today_iso = iso(date.today())

    # This query is pulling all overdue PM activities
    cur.execute(
        """
        SELECT trolley_id, MAX(next_due)
        FROM maintenance
        GROUP BY trolley_id
        HAVING MAX(next_due) <= ?
        ORDER BY MAX(next_due) ASC
        """,
        (today_iso,),
    )
    overdue_rows = cur.fetchall()

    # This query is pulling all upcoming PM in next 7 days
    upcoming_from = date.today() + timedelta(days=1)
    upcoming_to = date.today() + timedelta(days=7)
    cur.execute(
        """
        SELECT trolley_id, MAX(next_due)
        FROM maintenance
        GROUP BY trolley_id
        HAVING MAX(next_due) BETWEEN ? AND ?
        ORDER BY MAX(next_due) ASC
        """,
        (iso(upcoming_from), iso(upcoming_to)),
    )
    upcoming_rows = cur.fetchall()

    st.subheader("Overdue")
    if overdue_rows:
        for tid, nd in overdue_rows:
            st.markdown(
                f"<div class='reminder-overdue'><b>{tid}</b> — Due: {fmt_indian(nd)}</div>",
                unsafe_allow_html=True,
            )
            # Each button is letting the user mark a trolley as done
            if st.button(f"Mark Done {tid}"):
                cur.execute(
                    """
                    INSERT INTO maintenance (trolley_id, pm_date, next_due, created_at)
                    VALUES (?,?,?,?)
                    """,
                    (
                        tid,
                        iso(date.today()),
                        iso(date.today() + timedelta(days=PM_INTERVAL_DAYS)),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                st.success(f"{tid} is marked done")
                st.rerun()
    else:
        st.info("No overdue items.")

    st.markdown("### Upcoming (next 7 days)")
    if upcoming_rows:
        for tid, nd in upcoming_rows:
            st.markdown(
                f"<div class='reminder-upcoming'><b>{tid}</b> — Due: {fmt_indian(nd)}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No upcoming reminders in next 7 days.")

    st.markdown("</div>", unsafe_allow_html=True)   # form-card

    # This button is taking the user back to home
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    if st.button(t("btn_back_home")):
        st.session_state.page = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-reminder

# ----------------------------
# This section is rendering the TROLLEY LOOKUP page
# ----------------------------
elif st.session_state.page == "trolley":
    st.markdown('<div class="page-bg-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_trolley")}</div>', unsafe_allow_html=True)

    st.write("Enter a trolley ID to see its full history, last PM date, failures and cost.")
    lookup_id = st.text_input("Trolley ID to view:", key="lookup_id").strip()

    if st.button("Search Trolley"):
        if not lookup_id:
            st.error("Please enter a Trolley ID.")
        else:
            # This query is loading the maintenance history for one trolley
            df = pd.read_sql_query(
                """
                SELECT pm_date, next_due, failure_type, failure_note,
                       technician, amount, created_at
                FROM maintenance
                WHERE trolley_id = ?
                ORDER BY pm_date DESC
                """,
                conn,
                params=(lookup_id,),
            )

            # This query is checking if the trolley is scrapped
            cur.execute(
                """
                SELECT scrap_date, reason
                FROM scrapped
                WHERE trolley_id = ?
                ORDER BY scrap_date DESC
                LIMIT 1
                """,
                (lookup_id,),
            )
            scrap_row = cur.fetchone()

            if df.empty and not scrap_row:
                st.warning(f"No records found for trolley {lookup_id}.")
            else:
                st.subheader("Summary")

                last_pm_date = None
                next_due = None
                if not df.empty:
                    last_pm_date = df.iloc[0]["pm_date"]
                    next_due = df.iloc[0]["next_due"]

                failures_count = 0
                if not df.empty:
                    df_fail = df[df["failure_type"].notna()]
                    failures_count = len(df_fail)

                total_cost = sum_amount(df["amount"]) if not df.empty else 0.0

                today_d = date.today()
                failures_last_90 = 0
                if not df.empty:
                    # This loop is counting failures in the last 90 days
                    for _, row in df.iterrows():
                        try:
                            d = from_iso(row["pm_date"])
                        except Exception:
                            continue
                        if (today_d - d).days <= 90 and pd.notna(row["failure_type"]):
                            failures_last_90 += 1

                if next_due:
                    try:
                        nd = from_iso(next_due)
                        overdue = nd <= today_d
                    except Exception:
                        overdue = False
                else:
                    overdue = False

                # This block is calculating risk level
                risk_label = "Low"
                risk_color = "#dcfce7"
                if overdue or failures_last_90 >= 3:
                    risk_label = "High"
                    risk_color = "#fee2e2"
                elif failures_last_90 >= 1:
                    risk_label = "Medium"
                    risk_color = "#fef3c7"

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f"<div style='background:{risk_color};padding:10px;border-radius:8px;'>"
                        f"<b>Status:</b> {'Scrapped' if scrap_row else 'Active'}<br>"
                        f"<b>Risk level:</b> {risk_label}</div>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        "<div style='background:#eef2ff;padding:10px;border-radius:8px;'>"
                        f"<b>Last PM:</b> {fmt_indian(last_pm_date) if last_pm_date else '—'}<br>"
                        f"<b>Next due:</b> {fmt_indian(next_due) if next_due else '—'}</div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        "<div style='background:#f0f9ff;padding:10px;border-radius:8px;'>"
                        f"<b>Total failures:</b> {failures_count}<br>"
                        f"<b>Total cost:</b> {fmt_amount(total_cost)}</div>",
                        unsafe_allow_html=True,
                    )

                if scrap_row:
                    st.info(
                        f"🔧 This trolley is marked as **scrapped** on "
                        f"{fmt_indian(scrap_row[0])}. Reason: {scrap_row[1] or '—'}"
                    )

                if not df.empty:
                    st.subheader("Maintenance / Failure History")
                    df_display = df.copy()
                    df_display["pm_date"] = df_display["pm_date"].apply(fmt_indian)
                    df_display["next_due"] = df_display["next_due"].apply(fmt_indian)
                    df_display["amount"] = df_display["amount"].apply(fmt_amount)
                    st.dataframe(df_display, height=350)

    st.markdown("</div>", unsafe_allow_html=True)   # form-card

    # This button is taking the user back to home
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    if st.button(t("btn_back_home")):
        st.session_state.page = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-form

# ----------------------------
# This section is rendering the HISTORY / RECORDS view
# ----------------------------
elif st.session_state.page == "history":
    st.markdown('<div class="page-bg-history">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_history")}</div>', unsafe_allow_html=True)

    # This block is collecting filters
    filter_tid = st.text_input("Filter by Trolley ID (optional):").strip()

    # This query is building a year list from maintenance records
    year_df = pd.read_sql_query(
        """
        SELECT DISTINCT substr(pm_date,1,4) AS year
        FROM maintenance
        WHERE pm_date IS NOT NULL
        """,
        conn,
    )
    year_list = sorted([y for y in year_df["year"].dropna().tolist()])
    year_options = ["All"] + year_list if year_list else ["All"]

    colY, colM = st.columns(2)
    with colY:
        selected_year = st.selectbox("Year (for filters)", options=year_options)

    month_names = [
        "All",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    month_map = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    with colM:
        selected_month_name = st.selectbox("Month (for filters)", options=month_names)
    selected_month = (
        month_map.get(selected_month_name, None)
        if selected_month_name != "All"
        else None
    )

    def build_where(base_col: str, extra_tid_col: str | None = None):
        """
        This inner function is building a WHERE clause based on filters.

        Args:
            base_col (str): Column name on which year and month filters are applied.
            extra_tid_col (str | None): Optional column for trolley_id when different.

        Returns:
            tuple[str, list]: WHERE SQL snippet and parameters list.
        """
        clauses = []
        params: list = []

        if filter_tid:
            col_name = extra_tid_col if extra_tid_col else "trolley_id"
            clauses.append(f"{col_name} = ?")
            params.append(filter_tid)

        if selected_year != "All":
            clauses.append(f"strftime('%Y', {base_col}) = ?")
            params.append(selected_year)

        if selected_month is not None:
            clauses.append(f"strftime('%m', {base_col}) = ?")
            params.append(selected_month)

        where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""
        return where_sql, params

    # This block is creating tabs for different record types
    tabs = st.tabs(["Maintenance", "Failures", "Registry", "Scrapped"])

    # Maintenance tab
    with tabs[0]:
        where_sql, params = build_where("pm_date")
        query = (
            "SELECT trolley_id, pm_date, next_due, failure_type, failure_note, "
            "technician, amount, created_at FROM maintenance "
            f"{where_sql} ORDER BY pm_date DESC LIMIT 5000"
        )
        df_pm = pd.read_sql_query(query, conn, params=params)

        if not df_pm.empty:
            df_pm["pm_date"] = df_pm["pm_date"].apply(fmt_indian)
            df_pm["next_due"] = df_pm["next_due"].apply(fmt_indian)
            df_pm["amount_display"] = df_pm["amount"].apply(fmt_amount)
            st.dataframe(
                df_pm[
                    [
                        "trolley_id",
                        "pm_date",
                        "next_due",
                        "failure_type",
                        "failure_note",
                        "technician",
                        "amount_display",
                        "created_at",
                    ]
                ],
                height=400,
            )
            st.download_button(
                "Download maintenance CSV",
                df_pm.to_csv(index=False),
                file_name="maintenance_history.csv",
            )
            st.download_button(
                "Download maintenance Excel",
                df_to_excel_bytes(df_pm),
                file_name="maintenance_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No maintenance records found for selected filters.")

    # Failures tab
    with tabs[1]:
        where_sql, params = build_where("pm_date")
        # This query is restricting rows to ones that have a failure_type
        if where_sql:
            where_sql += " AND failure_type IS NOT NULL"
        else:
            where_sql = "WHERE failure_type IS NOT NULL"

        query = (
            "SELECT trolley_id, pm_date, failure_type, failure_note, "
            "technician, amount, created_at FROM maintenance "
            f"{where_sql} ORDER BY pm_date DESC LIMIT 5000"
        )
        df_fail = pd.read_sql_query(query, conn, params=params)

        if not df_fail.empty:
            df_fail["pm_date"] = df_fail["pm_date"].apply(fmt_indian)
            df_fail["amount_display"] = df_fail["amount"].apply(fmt_amount)
            st.dataframe(
                df_fail[
                    [
                        "trolley_id",
                        "pm_date",
                        "failure_type",
                        "failure_note",
                        "technician",
                        "amount_display",
                        "created_at",
                    ]
                ],
                height=400,
            )
            st.download_button(
                "Download failure CSV",
                df_fail.to_csv(index=False),
                file_name="failure_history.csv",
            )
            st.download_button(
                "Download failure Excel",
                df_to_excel_bytes(df_fail),
                file_name="failure_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No failure records found for selected filters.")

    # Registry tab
    with tabs[2]:
        where_sql, params = build_where("created_at", extra_tid_col="old_id")
        query = (
            "SELECT old_id, new_id, action, note, created_at "
            "FROM trolley_registry "
            f"{where_sql} ORDER BY created_at DESC LIMIT 5000"
        )
        df_reg = pd.read_sql_query(query, conn, params=params)

        if not df_reg.empty:
            st.dataframe(df_reg, height=400)
            st.download_button(
                "Download registry CSV",
                df_reg.to_csv(index=False),
                file_name="trolley_registry.csv",
            )
            st.download_button(
                "Download registry Excel",
                df_to_excel_bytes(df_reg),
                file_name="trolley_registry.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No registry records found for selected filters.")

    # Scrapped tab
    with tabs[3]:
        where_sql, params = build_where("scrap_date")
        query = (
            "SELECT trolley_id, scrap_date, reason, recorded_by, created_at "
            "FROM scrapped "
            f"{where_sql} ORDER BY scrap_date DESC LIMIT 5000"
        )
        df_scrap = pd.read_sql_query(query, conn, params=params)

        if not df_scrap.empty:
            df_scrap["scrap_date"] = df_scrap["scrap_date"].apply(fmt_indian)
            st.dataframe(df_scrap, height=400)
            st.download_button(
                "Download scrapped CSV",
                df_scrap.to_csv(index=False),
                file_name="scrapped_trolleys.csv",
            )
            st.download_button(
                "Download scrapped Excel",
                df_to_excel_bytes(df_scrap),
                file_name="scrapped_trolleys.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No scrapped trolleys for selected filters.")

    st.markdown("</div>", unsafe_allow_html=True)   # form-card

    # This button is taking the user back to home
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    if st.button(t("btn_back_home")):
        st.session_state.page = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-history

# ----------------------------
# This section is rendering the BACKUP & RESTORE DB screen
# ----------------------------
elif st.session_state.page == "backup_restore":
    st.markdown('<div class="page-bg-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="form-header">{t("page_backup")}</div>', unsafe_allow_html=True)

    st.info(
        "Download the current database file (`pm_demo.db`) as a backup.\n"
        "You are storing it on a pen drive / network folder / or mailing it to yourself.\n\n"
        "Later, you are restoring it by uploading that same .db file here."
    )

    # This block is offering a backup for download
    st.markdown("### 📀 Download Backup (Current Database)")
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            db_bytes = f.read()

        backup_default_name = f"pm_demo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        st.download_button(
            label="⬇ Download Current Database",
            data=db_bytes,
            file_name=backup_default_name,
            mime="application/octet-stream",
        )
        st.caption("You can rename this file after download. Please keep the .db extension.")
    else:
        st.error("Database file `pm_demo.db` not found. No data to backup yet.")

    st.markdown("---")

    # This block is handling restore from an uploaded .db file
    st.markdown("### ♻ Restore from Backup (.db file)")

    st.warning(
        "Restoring is OVERWRITING the current `pm_demo.db` with the file you upload.\n"
        "Please run this only when you are sure you are reverting to that backup."
    )

    uploaded_backup = st.file_uploader(
        "Upload a previous backup (.db file from this system):",
        type=["db"],
        key="restore_uploader",
    )

    if st.button("Restore Database"):
        if uploaded_backup is None:
            st.error("Please upload a backup .db file first.")
        else:
            # This block is overwriting pm_demo.db with uploaded contents
            new_bytes = uploaded_backup.read()
            with open(DB_PATH, "wb") as f:
                f.write(new_bytes)

            st.success("Database is restored successfully from uploaded backup.")
            st.info(
                "Now you are restarting the app: stop it in terminal and run "
                "`streamlit run app.py` again."
            )

    st.markdown("</div>", unsafe_allow_html=True)   # form-card

    # This button is taking the user back to home
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    if st.button("Back to Home", key="backup_home"):
        st.session_state.page = "home"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)   # page-bg-form
