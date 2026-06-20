import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- Configuration & Setup ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EdBKWTfCjK1gA7sxT2TwhSTcuE2zb_jA4oYP55c6wJU/edit"
LOGO_URL = "logo.png"

NETWORKS = ["AUSTRALIA", "NORTH AMERICA", "SOUTH AMERICA", "AFRICA", "EUROPE", "ASIA"]
CATEGORIES = ["Scholar Points", "Athlete Points", "Artist Points", "Leader Points"]

# --- Database Functions ---
@st.cache_data(ttl=60)
def load_data_from_sheets():
    """Connects to Google Sheets and reads the database."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1EdBKWTfCjK1gA7sxT2TwhSTcuE2zb_jA4oYP55c6wJU")
        worksheet = sh.get_worksheet(0)
        records = worksheet.get_all_records()
        
        if records:
            last_updated = records[-1].get("timestamp", "Not yet updated")
            try:
                dt = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
                last_updated = dt.strftime("%B %d, %Y")
            except:
                pass
        else:
            last_updated = "No updates yet"
            
        return {"last_updated": last_updated, "entries": records}
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return {"last_updated": "Error", "entries": []}

def save_data_to_sheets(new_entry):
    """Appends a new row of points to the Google Sheet."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        
        row_to_add = [
            new_entry["network"],
            new_entry["category"],
            int(new_entry["points"]),
            new_entry["student"],
            new_entry["competition"],
            new_entry["timestamp"]
        ]
        worksheet.append_row(row_to_add)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Submission Error: {e}")
        return False

def reset_data_in_sheets(network_to_reset):
    """Clears entries for a specific network or all networks, preserving headers."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        
        data = worksheet.get_all_values()
        if len(data) <= 1:
            return True # Nothing to delete (only headers remain)

        headers = data[0]
        rows = data[1:]
        
        worksheet.clear()
        worksheet.append_row(headers)
        
        if network_to_reset != "ALL":
            # Filter out the network we want to reset and append the rest back
            filtered_rows = [row for row in rows if row[0] != network_to_reset]
            if filtered_rows:
                worksheet.append_rows(filtered_rows)
                
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Reset Error: {e}")
        return False


# --- App Layout & Styling ---
st.set_page_config(page_title="KENSRI Score Board", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown { font-family: 'Poppins', sans-serif !important; }
.scoreboard-table { width: 100%; border-collapse: separate; border-spacing: 0 12px; margin-top: 20px; }
.scoreboard-table th { background-color: #000000; color: white; text-align: center; padding: 15px 10px; font-weight: 700; font-size: 16px; }
.scoreboard-table td { padding: 14px 15px; color: white; font-weight: 700; font-size: 18px; vertical-align: middle; }
.network-name { font-size: 20px !important; letter-spacing: 1px; text-shadow: 1px 1px 4px rgba(0,0,0,0.6); }
.score-box { background-color: #ffffff; color: #000000 !important; border-radius: 4px; padding: 6px 0; width: 100px; text-align: center; font-weight: 800; font-size: 18px; margin: 0 auto; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.15); text-shadow: none; }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image(LOGO_URL, width=120)
    except:
        st.write("*(Logo)*")
with col_title:
    st.markdown("<h1 style='color: #002060; font-weight: 800; font-size: 45px; margin-top: 10px;'>KENSRI SCHOOL & COLLEGE</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: white; background-color: #7F1D1D; padding: 12px; font-weight: 700; margin-top: 5px; font-size: 32px;'>NETWORK SCORE BOARD</h2>", unsafe_allow_html=True)

app_data = load_data_from_sheets()


# --- Session State for Authentication ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# --- Sidebar & Navigation ---
st.sidebar.title("Navigation")
st.sidebar.markdown("Welcome to the KENSRI Network Score Board.")
st.sidebar.markdown("---")

if not st.session_state.admin_logged_in:
    # Stealth Admin Login
    st.sidebar.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    password_attempt = st.sidebar.text_input("Admin Access", type="password", placeholder="...") 
    if password_attempt == "admin123":
        st.session_state.admin_logged_in = True
        st.rerun()
    view_mode = "Public Scoreboard"
else:
    # Admin is logged in
    st.sidebar.success("✅ Logged in as Admin")
    if st.sidebar.
