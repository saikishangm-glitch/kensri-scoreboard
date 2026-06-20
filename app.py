import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- Configuration & Setup ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EdBKWTfCjK1gA7sxT2TwhSTcuE2zb_jA4oYP55c6wJU/edit"
LOGO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS4CIdhBTkIUp9FpB7aaWpBMZkHMJS2RzOyXQ&s"

NETWORKS = ["AUSTRALIA", "NORTH AMERICA", "SOUTH AMERICA", "AFRICA", "EUROPE", "ASIA"]
CATEGORIES = ["Scholar Points", "Athlete Points", "Artist Points", "Leader Points"]

@st.cache_data(ttl=60)
def load_data_from_sheets():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_key("1EdBKWTfCjK1gA7sxT2TwhSTcuE2zb_jA4oYP55c6wJU")
        worksheet = sh.get_worksheet(0)
        records = worksheet.get_all_records()
        return {"last_updated": datetime.now().strftime("%B %d, %Y"), "entries": records}
    except Exception as e:
        return {"last_updated": "Error", "entries": []}

def save_data_to_sheets(new_entry):
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        row_to_add = [new_entry["network"], new_entry["category"], int(new_entry["points"]), new_entry["student"], new_entry["competition"], new_entry["timestamp"]]
        worksheet.append_row(row_to_add)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- UI Setup ---
st.set_page_config(page_title="KENSRI Score Board", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
html, body { font-family: 'Poppins', sans-serif !important; }
.scoreboard-table { width: 100%; border-collapse: separate; border-spacing: 0 12px; margin-top: 20px; }
.scoreboard-table th { background-color: #000000; color: white; padding: 15px; text-align: center; }
.scoreboard-table td { padding: 14px; background-color: #f9f9f9; font-weight: 700; text-align: center; }
.score-box { background-color: #333; color: white; border-radius: 4px; padding: 5px; width: 80px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# Header
col_logo, col_title = st.columns([1, 5])
with col_logo: st.image(LOGO_URL, width=120)
with col_title: st.markdown("<h1 style='color: #002060; font-weight: 800;'>KENSRI SCHOOL & COLLEGE</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: white; background-color: #7F1D1D; padding: 10px;'>NETWORK SCORE BOARD</h2>", unsafe_allow_html=True)

app_data = load_data_from_sheets()

# Sidebar (Stealth)
st.sidebar.title("Navigation")
st.sidebar.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
password_attempt = st.sidebar.text_input(" ", type="password", placeholder="...") 
view_mode = "Admin Panel" if password_attempt == "admin123" else "Public Scoreboard"

# Logic
if view_mode == "Public Scoreboard":
    board = {net: {cat: 0 for cat in CATEGORIES} for net in NETWORKS}
    for entry in app_data["entries"]:
        if entry["network"] in board and entry["category"] in board[entry["network"]]:
            board[entry["network"]][entry["category"]] += int(entry["points"])
    
    table_html = "<table class='scoreboard-table'><thead><tr><th>Network</th>" + "".join([f"<th>{c}</th>" for c in CATEGORIES]) + "<th>Total</th></tr></thead><tbody>"
    for net in NETWORKS:
        row_sum = sum(board[net].values())
        table_html += f"<tr><td>{net}</td>" + "".join([f"<td>{board[net][cat]}</td>" for cat in CATEGORIES]) + f"<td>{row_sum}</td></tr>"
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    st.markdown("### 🏆 Recent Activity")
    for entry in reversed(app_data["entries"][-10:]):
        st.info(f"{entry['network']} | **{entry['student']}**: {entry['competition']} ({entry['points']} pts)")

elif view_mode == "Admin Panel":
    st.subheader("Admin Control Panel")
    tab1, tab2 = st.tabs(["Add/Deduct Points", "Reset Operations"])
    
    with tab1:
        with st.form("points_form"):
            action = st.radio("Action", ["Add Points", "Deduct Points (Misconduct)"])
            col1, col2 = st.columns(2)
            net = col1.selectbox("Network", NETWORKS)
            cat = col1.selectbox("Category", CATEGORIES)
            pts = col2.number_input("Points", min_value=1)
            name = col2.text_input("Student Name")
            desc = st.text_input("Details (Competition/Reason)")
            
            if st.form_submit_button("Submit"):
                final_pts = -abs(pts) if action == "Deduct Points (Misconduct)" else abs(pts)
                save_data_to_sheets({"network": net, "category": cat, "points": final_pts, "student": name, "competition": desc, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.success("Transaction Complete")

    with tab2:
        st.warning("⚠️ Careful! Resetting clears the history for the selected scope.")
        reset_scope = st.radio("Choose Reset Scope", ["Reset Continent", "Reset All (Global Reset)"])
        
        if reset_scope == "Reset Continent":
            target_net = st.selectbox("Select Network to Reset", NETWORKS)
            confirm = st.checkbox(f"Confirm reset of {target_net}")
            if st.button("Execute Continent Reset") and confirm:
                # Calculate current totals for this network and append negative rows
                for cat in CATEGORIES:
                    current_total = sum([e['points'] for e in app_data['entries'] if e['network'] == target_net and e['category'] == cat])
                    if current_total != 0:
                        save_data_to_sheets({"network": target_net, "category": cat, "points": -current_total, "student": "SYSTEM", "competition": "Reset/Correction", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.success(f"{target_net} has been reset.")
        
        else: # Reset All
            confirm_all = st.checkbox("I verify that I want to wipe ALL scores globally.")
            if st.button("Execute GLOBAL RESET") and confirm_all:
                for net in NETWORKS:
                    for cat in CATEGORIES:
                        current_total = sum([e['points'] for e in app_data['entries'] if e['network'] == net and e['category'] == cat])
                        if current_total != 0:
                            save_data_to_sheets({"network": net, "category": cat, "points": -current_total, "student": "SYSTEM", "competition": "Global Reset", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                st.success("System fully reset.")
