# app.py
import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound, APIError

# ---------------- Page & Theme ----------------
st.set_page_config(page_title="Kitaab Un Najaah Attendance", page_icon="📖", layout="centered")
BACKGROUND = "#FDF5EA"; OLIVE_LIGHT = "#C3CBA6"; OLIVE_DARK = "#4A5C3D"
st.markdown(f"""
<style>
  body {{ background-color: {BACKGROUND}; }}
  .title {{ text-align:center; font-size:36px; font-weight:800; color:{OLIVE_DARK}; letter-spacing:1px; }}
  .subtitle {{ text-align:center; font-size:18px; color:{OLIVE_DARK}; margin-bottom:1rem; }}
  .stTextInput > div > div > input {{ background-color:{OLIVE_LIGHT}22; border-radius:10px; }}
  .stButton>button {{ background-color:{OLIVE_LIGHT}; color:white; font-weight:700; border-radius:10px; padding:0.6rem 1.2rem; border:0; }}
  .stButton>button:hover {{ background-color:{OLIVE_DARK}; color:white; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>KITAAB UN NAJAAH</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Attendance Registration</div>", unsafe_allow_html=True)

# ---------------- Auth ----------------
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    info = dict(st.secrets["gcp_service_account"])
    # Fix common '\n' issue inside TOML
    if "\\n" in info.get("private_key", ""):
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

def open_spreadsheet(spreadsheet_id: str):
    gc = get_gspread_client()
    try:
        return gc.open_by_key(spreadsheet_id)
    except SpreadsheetNotFound as e:
        sa = st.secrets["gcp_service_account"]["client_email"]
        raise RuntimeError(
            f"Spreadsheet not found. Check the ID and share the Sheet with {sa} (Editor)."
        ) from e
    except APIError as e:
        # Google sometimes returns 404 as APIError
        msg = str(e)
        if "404" in msg or "notFound" in msg:
            sa = st.secrets["gcp_service_account"]["client_email"]
            raise RuntimeError(
                f"Spreadsheet not found or not shared. Share with {sa} and verify the ID."
            ) from e
        raise

def ensure_worksheet(ss, title: str):
    try:
        return ss.worksheet(title)
    except WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=1000, cols=3)
        ws.append_row(["Name", "Phone Number"], value_input_option="USER_ENTERED")
        return ws

# ---------------- UI ----------------
date_display = datetime.now().strftime("%d-%m-%y")  # for text
sheet_title  = datetime.now().strftime("%d %m %y")  # tab name
st.write(f"**Marking attendance for {date_display}**")

with st.form("attendance_form", border=True):
    name  = st.text_input("Enter Name", placeholder="e.g. Ali Hasan")
    phone = st.text_input("Enter Phone Number", placeholder="e.g. +65 8123 4567")
    submitted = st.form_submit_button("Submit")

if submitted:
    if not name.strip() or not phone.strip():
        st.error("Please fill in both fields before submitting.")
    else:
        try:
            ss_id = st.secrets["app_settings"]["spreadsheet_id"]
            ss = open_spreadsheet(ss_id)
            ws = ensure_worksheet(ss, sheet_title)
            ws.append_row([name.strip(), phone.strip()], value_input_option="USER_ENTERED")
            st.success(f"Attendance marked for {name} on {date_display} ✅")
        except Exception as e:
            st.error(f"Google Sheets error: {e}")
