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
    if st.sidebar.button("Log Out & Return to Public View"):
        st.session_state.admin_logged_in = False
        st.rerun()
    view_mode = "Admin Panel"


# --- View Logic: Public Scoreboard ---
if view_mode == "Public Scoreboard":
    st.markdown(f"<p style='font-size: 18px; font-weight: 600; color: #333;'>📅 <b>Date updated on:</b> <span style='color: #7F1D1D; font-weight: 700;'>{app_data['last_updated']}</span></p>", unsafe_allow_html=True)
    
    board = {net: {cat: 0 for cat in CATEGORIES} for net in NETWORKS}
    for entry in app_data["entries"]:
        if entry["network"] in board and entry["category"] in board[entry["network"]]:
            board[entry["network"]][entry["category"]] += int(entry["points"])
        
    network_colors = {
        "AUSTRALIA": "#023020", "NORTH AMERICA": "#0BA3FF", "SOUTH AMERICA": "#FFFF2E",
        "AFRICA": "#7030A0", "EUROPE": "#000080", "ASIA": "#FF2600"
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
    
    # Render Achievements (Handling Negative Points)
    st.markdown("<h3 style='color: #002060; font-weight: 700;'>🏆 Recent Activities</h3>", unsafe_allow_html=True)
    if app_data["entries"]:
        for entry in reversed(app_data["entries"]):
            if int(entry['points']) < 0:
                st.warning(f"⚠️ **{entry['student']}** — {entry['competition']}. **Lost {abs(int(entry['points']))}** {entry['category']} points for **{entry['network']}**.")
            else:
                st.info(f"🏅 **{entry['student']}** — **{entry['competition']}**! Earned **{entry['points']}** {entry['category']} for **{entry['network']}**.")
    else:
        st.write("*No achievement milestones recorded yet.*")


# --- View Logic: Admin Panel ---
elif view_mode == "Admin Panel":
    st.subheader("🛠️ Admin Dashboard")
    
    tab_award, tab_deduct, tab_reset = st.tabs(["🌟 Award Points", "⚠️ Deduct Points", "⚙️ Database Control"])
    
    # TAB 1: AWARD POINTS
    with tab_award:
        with st.form("add_points_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_network = st.selectbox("Select Network", NETWORKS, key="award_net")
                selected_category = st.selectbox("Select Category", CATEGORIES, key="award_cat")
                points = st.number_input("Points to Award", min_value=1, step=1, key="award_pts")
            with col2:
                student_name = st.text_input("Student Name", key="award_stu")
                
            st.markdown("#### Achievement Details")
            achievement_type = st.radio("Type of Achievement", ["Secured a Place / Won", "Participation"], key="award_type")
            
            col3, col4 = st.columns(2)
            with col3:
                event_name = st.text_input("Event Name (e.g., Inter-School Debate)", key="award_evt")
            with col4:
                event_date = st.date_input("Date of Event", key="award_dt")
                
            place_secured = ""
            if achievement_type == "Secured a Place / Won":
                place_secured = st.text_input("Place Secured (e.g., 1st, Gold)", key="award_place")
                
            submitted = st.form_submit_button("Publish & Save Score Updates", type="primary")
            
            if submitted:
                if student_name.strip() and event_name.strip():
                    if achievement_type == "Secured a Place / Won" and not place_secured.strip():
                        st.error("Submission rejected: Please specify the place secured.")
                    else:
                        date_str = event_date.strftime("%d/%m/%Y")
                        narrative = f"{place_secured} Place in {event_name} on {date_str}" if achievement_type == "Secured a Place / Won" else f"Participated in {event_name} on {date_str}"
                            
                        new_entry = {
                            "network": selected_network, "category": selected_category, "points": points,
                            "student": student_name, "competition": narrative, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        if save_data_to_sheets(new_entry):
                            st.success("🎉 Data safely written!")
                else:
                    st.error("Submission rejected: Please fill all required fields.")

    # TAB 2: DEDUCT POINTS
    with tab_deduct:
        with st.form("deduct_points_form"):
            st.markdown("Use this panel to log misconduct or rule violations. Points will be subtracted.")
            col1, col2 = st.columns(2)
            with col1:
                deduct_network = st.selectbox("Select Network", NETWORKS, key="deduct_net")
                deduct_category = st.selectbox("Select Category to Deduct From", CATEGORIES, key="deduct_cat")
                deduct_points = st.number_input("Points to Deduct", min_value=1, step=1, key="deduct_pts")
            with col2:
                deduct_student = st.text_input("Student Name (Optional)", key="deduct_stu")
                deduct_reason = st.text_input("Reason / Violation Event", key="deduct_reason")
            
            deduct_submitted = st.form_submit_button("Apply Deduction", type="primary")
            
            if deduct_submitted:
                if deduct_reason.strip():
                    student = deduct_student.strip() if deduct_student.strip() else "Team Penalty"
                    new_entry = {
                        "network": deduct_network, "category": deduct_category, "points": -deduct_points, # Save as negative
                        "student": student, "competition": f"Penalty: {deduct_reason}", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    if save_data_to_sheets(new_entry):
                        st.success(f"⚠️ Penalty applied: {deduct_points} points deducted from {deduct_network}.")
                else:
                    st.error("Submission rejected: Please provide a reason for the deduction.")

    # TAB 3: RESET DATABASE
    with tab_reset:
        st.markdown("#### Scoreboard Reset Controls")
        st.warning("⚠️ **Warning:** Resetting will permanently delete the selected entries from the Google Sheet. This action cannot be undone.")
        
        reset_target = st.selectbox("Select Target to Reset", ["ALL"] + NETWORKS)
        
        # Checkbox confirmation before allowing the reset button to be clicked
        confirm_reset = st.checkbox("I understand the consequences and want to proceed with the reset.")
        
        if st.button("Wipe Database Data", type="primary", disabled=not confirm_reset):
            if reset_data_in_sheets(reset_target):
                if reset_target == "ALL":
                    st.success("💥 The entire scoreboard has been reset.")
                else:
                    st.success(f"💥 All records for **{reset_target}** have been erased.")
