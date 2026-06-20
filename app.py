import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuration & Setup ---
# 🚨 PASTE YOUR COPIED GOOGLE SHEET LINK HERE 🚨
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit"

NETWORKS = ["AUSTRALIA", "NORTH AMERICA", "SOUTH AMERICA", "AFRICA", "EUROPE", "ASIA"]
CATEGORIES = ["Scholar Points", "Athlete Points", "Artist Points", "Leader Points"]

@st.cache_data(ttl=60) # Refreshes data from the cloud every 60 seconds
def load_data_from_sheets():
    """Connects to Google Sheets and reads the database."""
    try:
        # We use Streamlit's secure secrets management for credentials when online
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        records = worksheet.get_all_records()
        
        # Find the latest update timestamp
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
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url(GOOGLE_SHEET_URL)
    worksheet = sh.get_worksheet(0)
    
    # Order must match your Google Sheet column headers
    row_to_add = [
        new_entry["network"],
        new_entry["category"],
        int(new_entry["points"]),
        new_entry["student"],
        new_entry["competition"],
        new_entry["timestamp"]
    ]
    worksheet.append_row(row_to_add)
    st.cache_data.clear() # Clear cache so changes show up instantly

# --- App Layout & Styling ---
st.set_page_config(page_title="KENSRI Score Board", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown { font-family: 'Poppins', sans-serif !important; }
.scoreboard-table { width: 100%; border-collapse: separate; border-spacing: 0 12px; margin-top: 20px; }
.scoreboard-table th { background-color: #000000; color: white; text-align: center; padding: 15px 10px; font-weight: 700; font-size: 16px; }
.scoreboard-table td { padding: 14px 15px; color: white; font-weight: 700; font-size: 18px; vertical-align: middle; }
.network-name { 
    font-size: 20px !important; 
    letter-spacing: 1px; 
    text-shadow: 1px 1px 4px rgba(0,0,0,0.6); /* Added shadow for readability on bright colors */
}
.score-box { background-color: #ffffff; color: #000000 !important; border-radius: 4px; padding: 6px 0; width: 100px; text-align: center; font-weight: 800; font-size: 18px; margin: 0 auto; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.15); text-shadow: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #002060; font-weight: 800; font-size: 52px; margin-bottom: 0px;'>KENSRI SCHOOL & COLLEGE</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: white; background-color: #7F1D1D; padding: 12px; font-weight: 700; margin-top: 5px; font-size: 32px;'>NETWORK SCORE BOARD</h2>", unsafe_allow_html=True)

app_data = load_data_from_sheets()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
view_mode = st.sidebar.radio("Select View:", ["Public Scoreboard", "Admin Panel"])
st.sidebar.markdown("---")

# ==========================================
# FRONT END: PUBLIC VIEW
# ==========================================
if view_mode == "Public Scoreboard":
    st.markdown(f"<p style='font-size: 18px; font-weight: 600; color: #333;'>📅 <b>Date updated on:</b> <span style='color: #7F1D1D; font-weight: 700;'>{app_data['last_updated']}</span></p>", unsafe_allow_html=True)
    
    board = {net: {cat: 0 for cat in CATEGORIES} for net in NETWORKS}
    for entry in app_data["entries"]:
        if entry["network"] in board and entry["category"] in board[entry["network"]]:
            board[entry["network"]][entry["category"]] += int(entry["points"])
        
    # YOUR NEW CUSTOM COLOR PALETTE
    network_colors = {
        "AUSTRALIA": "#023020",      # Dark Green
        "NORTH AMERICA": "#0BA3FF",  # Light blue
        "SOUTH AMERICA": "#FFFF2E",  # Yellow
        "AFRICA": "#7030A0",         # Royal Purple
        "EUROPE": "#000080",         # Navy Blue
        "ASIA": "#FF2600"            # Orange
    }
    
    table_html = "<table class='scoreboard-table'><thead><tr><th style='text-align: left; padding-left: 15px; width: 25%;'>Network</th>"
    for cat in CATEGORIES: table_html += f"<th>{cat}</th>"
    table_html += "<th>Total Score</th></tr></thead><tbody>"
    
    for net in NETWORKS:
        row_bg = network_colors[net]
        total_score = sum(board[net].values())
        table_html += f"<tr style='background-color: {row_bg};'><td class='network-name'>{net}</td>"
        for cat in CATEGORIES:
            table_html += f"<td><div class='score-box'>{board[net][cat]}</div></td>"
        table_html += f"<td><div class='score-box'>{total_score}</div></td></tr>"
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<h3 style='color: #002060; font-weight: 700;'>🏆 Recent Achievements</h3>", unsafe_allow_html=True)
    if app_data["entries"]:
        for entry in reversed(app_data["entries"]):
            st.info(f"🏅 **{entry['student']}** won **{entry['competition']}**! Earned **{entry['points']}** {entry['category']} for **{entry['network']}**.")
    else:
        st.write("*No achievement milestones recorded yet.*")

# ==========================================
# BACK END: ADMIN VIEW
# ==========================================
elif view_mode == "Admin Panel":
    password_attempt = st.sidebar.text_input("Enter Admin Password", type="password")
    
    if password_attempt == "admin123":
        st.sidebar.success("Access Verified")
        st.subheader("Data Entry Panel")
        
        with st.form("add_points_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_network = st.selectbox("Select Network", NETWORKS)
                selected_category = st.selectbox("Select Category", CATEGORIES)
                points = st.number_input("Points to Award", min_value=1, step=1)
            with col2:
                student_name = st.text_input("Student Name")
                competition_name = st.text_input("Competition Name / Event Name")
                
            submitted = st.form_submit_button("Publish & Save Score Updates")
            
            if submitted:
                if student_name.strip() and competition_name.strip():
                    new_entry = {
                        "network": selected_network,
                        "category": selected_category,
                        "points": points,
                        "student": student_name,
                        "competition": competition_name,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_data_to_sheets(new_entry)
                    st.success("🎉 Data safely written to Google Sheets! Switch back to view changes.")
                else:
                    st.error("Submission rejected: Please fill all fields.")
    elif password_attempt != "":
        st.sidebar.error("Incorrect Credentials")
    else:
        st.warning("🔒 Enter administrative credentials on the sidebar menu to alter network metrics.")