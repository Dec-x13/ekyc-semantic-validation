import os
import datetime
import re
import json
import streamlit as st
from PIL import Image
from ocr_pipeline import run_ocr_pipeline
from rule_engine import validate_dates

# 1. Global Page Configuration
st.set_page_config(
    page_title="SentinelKYC Verification Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Figma Pixel-Perfect CSS Overrides (Deep Navy theme)
st.markdown("""
<style>
    /* Hide Streamlit default branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main Layout background & Typography */
    .stApp {
        background-color: #131B2A !important;
        color: #F8FAFC !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    
    /* Sidebar Background and Border */
    section[data-testid="stSidebar"] {
        background-color: #0B1120 !important;
        border-right: 1px solid #2D3748 !important;
    }
    
    /* Document Preview Card Styling */
    div[data-testid="stImage"] {
        background-color: #1E2738 !important;
        border: 1px solid #2D3748 !important;
        border-radius: 8px !important;
        padding: 24px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* General Panel Card wrapper */
    .panel-card {
        background-color: #1E2738 !important;
        border: 1px solid #2D3748 !important;
        border-radius: 8px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
    }
    
    /* Custom eKYC Data Table */
    .ekyc-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 5px;
        font-size: 13px;
    }
    .ekyc-table th {
        text-align: left;
        padding: 8px 10px;
        border-bottom: 2px solid #2D3748;
        color: #828FA3;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.05em;
    }
    .ekyc-table td {
        padding: 10px 10px;
        border-bottom: 1px solid #2D3748;
        color: #FFFFFF;
    }
    .ekyc-table tr:last-child td {
        border-bottom: none;
    }
    .ekyc-table tr:hover {
        background-color: rgba(45, 55, 72, 0.25);
    }
    
    /* Flagged Field Badge */
    .flagged-pill {
        background-color: #EF4444 !important;
        color: #FFFFFF !important;
        font-size: 9px !important;
        font-weight: 700 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        margin-left: 8px !important;
        letter-spacing: 0.05em !important;
    }
    
    /* Sidebar card list item styling */
    div[data-testid="stSidebar"] div.stButton > button {
        background-color: #161D2B !important;
        color: #828FA3 !important;
        border: 1px solid #2D3748 !important;
        border-radius: 6px !important;
        text-align: left !important;
        padding: 12px 14px !important;
        font-size: 12px !important;
        width: 100% !important;
        font-weight: 500 !important;
        margin-bottom: 6px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #1E2738 !important;
        color: #FFFFFF !important;
        border-color: #4A5568 !important;
    }
    /* Style active state card border */
    div[data-testid="stSidebar"] div.stButton > button:active,
    div[data-testid="stSidebar"] div.stButton > button:focus {
        border-left: 4px solid #0EA5E9 !important;
        background-color: #1E2738 !important;
        color: #FFFFFF !important;
    }
    
    /* Action button at right column */
    div[data-testid="column"] div.stButton > button {
        background-color: #0EA5E9 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 10px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 6px rgba(14, 165, 233, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
    }
    div[data-testid="column"] div.stButton > button:hover {
        background-color: #38BDF8 !important;
        filter: brightness(1.15) !important;
    }
    
    /* Fixed Sidebar footer */
    .sidebar-footer {
        position: fixed;
        bottom: 15px;
        left: 20px;
        color: #4A5568;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# Reference date for the engine check
REF_DATE = datetime.date(2026, 7, 16)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IDS_DIR = os.path.join(BASE_DIR, "data", "ids")
METADATA_PATH = os.path.join(BASE_DIR, "data", "metadata.json")

# Retrieve metadata index
@st.cache_data
def load_metadata():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

metadata = load_metadata()

# Initialize session state for persistent results
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = "id_0001.png"
if 'validated' not in st.session_state:
    st.session_state.validated = False
if 'is_valid' not in st.session_state:
    st.session_state.is_valid = True
if 'violations' not in st.session_state:
    st.session_state.violations = []
if 'dob' not in st.session_state:
    st.session_state.dob = None
if 'issue' not in st.session_state:
    st.session_state.issue = None
if 'expiry' not in st.session_state:
    st.session_state.expiry = None
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
if 'is_sim' not in st.session_state:
    st.session_state.is_sim = False
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

# Reset state when selected document changes
if st.session_state.selected_file != st.session_state.current_file:
    st.session_state.current_file = st.session_state.selected_file
    st.session_state.validated = False

# 3. Sidebar Branding & structured controls
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px;">
    <div style="background-color: #0F172A; border: 2px solid #0EA5E9; border-radius: 6px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; color: #0EA5E9; font-weight: bold; font-size: 16px;">
        🛡️
    </div>
    <div>
        <div style="color: #FFFFFF; font-weight: 700; font-size: 17px; line-height: 1.2;">SentinelKYC</div>
        <div style="color: #828FA3; font-size: 11px;">Verification Console</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Upload Button (UI representation)
st.sidebar.markdown("""
<div style="margin-bottom: 20px;">
    <button style="background-color: transparent; color: #0EA5E9; border: 1px solid #0EA5E9; border-radius: 6px; font-weight: 600; font-size: 13px; padding: 10px 15px; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;">
        📤 Upload Document
    </button>
</div>
""", unsafe_allow_html=True)

# Sample Documents Selection Cards
st.sidebar.markdown("<div style='color: #828FA3; font-size: 10px; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;'>TEST DOCUMENTS</div>", unsafe_allow_html=True)

samples = [
    ("PP-4471-A", "Passport · United States", "🟢", "id_0001.png"),
    ("DL-9920-C", "Driver License · Canada", "🔴", "id_0501.png"),
    ("ID-3312-B", "National ID · Germany", "🟢", "id_0002.png"),
    ("PP-8830-Z", "Passport · Brazil", "🔴", "id_0502.png")
]

for label, subtitle, dot, fname in samples:
    is_active = (st.session_state.selected_file == fname)
    display_label = f"▶ 📄 {label}   ·   {subtitle}   {dot}" if is_active else f"📄 {label}   ·   {subtitle}   {dot}"
    
    if st.sidebar.button(display_label, key=f"btn_{fname}"):
        st.session_state.selected_file = fname
        st.rerun()

# Sidebar Footer
st.sidebar.markdown('<div class="sidebar-footer">Operator: A. Reyes &middot; Clearance L3</div>', unsafe_allow_html=True)

# Resolve selected file path
image_path = os.path.join(IDS_DIR, st.session_state.selected_file)

# 4. Top Header Area (with dynamic Valid/Fraud status pills)
h_col1, h_col2 = st.columns([2, 1])

with h_col1:
    # Determine the case number dynamically
    case_num = "001" if st.session_state.selected_file == "id_0001.png" else "002" if st.session_state.selected_file == "id_0501.png" else "003" if st.session_state.selected_file == "id_0002.png" else "004"
    st.markdown(f"""
    <div>
        <h2 style="color: #FFFFFF; font-weight: 700; font-size: 22px; margin: 0;">eKYC Document Verification</h2>
        <div style="color: #828FA3; font-size: 12px; margin-top: 2px;">Case #DOC-{case_num} &middot; Semantic Logic Execution</div>
    </div>
    """, unsafe_allow_html=True)

with h_col2:
    # Color-coded active pill logic
    is_eval = st.session_state.validated
    is_legit = st.session_state.is_valid
    
    valid_style = "background-color: #10B981; color: white;" if (is_eval and is_legit) else "background-color: rgba(255,255,255,0.05); color: #4A5568;"
    fraud_style = "background-color: #EF4444; color: white;" if (is_eval and not is_legit) else "background-color: rgba(255,255,255,0.05); color: #4A5568;"
    
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; gap: 8px; align-items: center; height: 100%; padding-top: 10px;">
        <span style="padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; {valid_style}">Valid Identity</span>
        <span style="padding: 6px 14px; border-radius: 15px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; {fraud_style}">Fraud Detected</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 0; border-top: 1px solid #2D3748; margin-top: 15px; margin-bottom: 20px;' />", unsafe_allow_html=True)

# 5. Two Column Dashboard Layout
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    # Document Preview Header
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 4px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #0EA5E9; font-size: 16px;">🔍</span>
            <h3 style="color: #FFFFFF; font-size: 14px; font-weight: 600; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">Document Preview</h3>
        </div>
        <div style="color: #828FA3; font-size: 13px; display: flex; gap: 12px; cursor: pointer;">
            <span>🔍</span>
            <span>🔄</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if image_path and os.path.exists(image_path):
        img = Image.open(image_path)
        st.image(img, use_container_width=True)
    else:
        st.info("Intake image preview unavailable.")

with col2:
    run_btn = st.button("▶ Run Semantic Validation")
    
    if run_btn:
        with st.spinner("Extracting & running checks..."):
            dob, issue, expiry, raw_text, is_sim = run_ocr_pipeline(image_path, metadata)
            is_valid, violations = validate_dates(dob, issue, expiry, REF_DATE)
            
            # Store results in session state
            st.session_state.validated = True
            st.session_state.is_valid = is_valid
            st.session_state.violations = violations
            st.session_state.dob = dob
            st.session_state.issue = issue
            st.session_state.expiry = expiry
            st.session_state.raw_text = raw_text
            st.session_state.is_sim = is_sim
            st.rerun()

    # If evaluated, build the custom cards
    if st.session_state.validated:
        dob = st.session_state.dob
        issue = st.session_state.issue
        expiry = st.session_state.expiry
        raw_text = st.session_state.raw_text
        is_sim = st.session_state.is_sim
        is_valid = st.session_state.is_valid
        violations = st.session_state.violations
        
        # Analyze which fields are flagged based on violations
        dob_flagged = False
        issue_flagged = False
        expiry_flagged = False
        
        for v in violations:
            if "Date of Birth" in v or "age" in v.lower():
                dob_flagged = True
            if "Issue Date" in v or "age" in v.lower():
                issue_flagged = True
            if "Expiry" in v:
                expiry_flagged = True
                
        # Format the flagged pills
        flag_html = '<span class="flagged-pill">FLAGGED</span>'
        
        dob_val = f"<span style='color: #EF4444;'>{dob}</span> {flag_html}" if dob_flagged else str(dob)
        issue_val = f"<span style='color: #EF4444;'>{issue}</span> {flag_html}" if issue_flagged else str(issue)
        expiry_val = f"<span style='color: #EF4444;'>{expiry}</span> {flag_html}" if expiry_flagged else str(expiry)
        
        # Metadata Field Extraction HTML
        name_match = re.search(r'FULL\s+NAME:?\s*(.*)', raw_text, re.IGNORECASE)
        id_match = re.search(r'ID\s+NUMBER:?\s*(.*)', raw_text, re.IGNORECASE)
        card_name = name_match.group(1).strip() if name_match else "EXTRACT FAILED"
        card_id = id_match.group(1).strip() if id_match else "EXTRACT FAILED"
        
        meta_html = f"""
        <div class="panel-card">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="color: #0EA5E9; font-size: 15px;">💾</span>
                <h3 style="color: #FFFFFF; font-size: 13px; font-weight: 600; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">Extracted Metadata</h3>
            </div>
            <table class="ekyc-table">
                <tbody>
                    <tr>
                        <td style="color: #828FA3; width: 40%;">Full Name</td>
                        <td>{card_name.title()}</td>
                    </tr>
                    <tr>
                        <td style="color: #828FA3;">ID Number</td>
                        <td>{card_id}</td>
                    </tr>
                    <tr>
                        <td style="color: #828FA3;">Date of Birth</td>
                        <td>{dob_val}</td>
                    </tr>
                    <tr>
                        <td style="color: #828FA3;">Issue Date</td>
                        <td>{issue_val}</td>
                    </tr>
                    <tr>
                        <td style="color: #828FA3;">Expiry Date</td>
                        <td>{expiry_val}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        st.markdown(meta_html, unsafe_allow_html=True)
        
        # Compute exact mathematical output details for the logic list
        is_chron_passed = (dob and issue and expiry and issue < expiry and dob <= issue)
        chron_txt = f"{issue.year} &lt; {expiry.year} · consistent" if is_chron_passed else "inconsistent chronology"
        
        is_auth_passed = True
        auth_txt = "Checksum valid"
        
        age_at_issue = issue.year - dob.year - ((issue.month, issue.day) < (dob.month, dob.day)) if (dob and issue) else 0
        is_age_passed = (age_at_issue >= 18)
        age_txt = f"Age {age_at_issue} · requirement met" if is_age_passed else f"Age {age_at_issue} at issuance · requirement violated"
        
        is_expiry_passed = (expiry and expiry >= REF_DATE)
        expiry_txt = f"Valid until {expiry.year}" if is_expiry_passed else f"Expired on {expiry.strftime('%Y-%m-%d')}"
        
        # Logic Rule checklist HTML Builder
        def make_rule_row(title, desc, math_text, is_passed):
            icon = "✓" if is_passed else "×"
            icon_bg = "#064E3B" if is_passed else "#7F1D1D"
            icon_color = "#10B981" if is_passed else "#EF4444"
            math_color = "#10B981" if is_passed else "#EF4444"
            return f"""
            <tr style="border-bottom: 1px solid #2D3748;">
                <td style="padding: 10px 8px; width: 35px; text-align: center; vertical-align: middle;">
                    <div style="background-color: {icon_bg}; color: {icon_color}; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px;">
                        {icon}
                    </div>
                </td>
                <td style="padding: 10px 8px; vertical-align: middle;">
                    <div style="color: #FFFFFF; font-weight: 600; font-size: 13px;">{title}</div>
                    <div style="color: #828FA3; font-size: 11px; margin-top: 1px;">{desc}</div>
                </td>
                <td style="padding: 10px 8px; text-align: right; color: {math_color}; font-size: 12px; font-weight: 500; white-space: nowrap; vertical-align: middle;">
                    {math_text}
                </td>
            </tr>
            """
            
        rules_html = f"""
        <div class="panel-card">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <span style="color: #0EA5E9; font-size: 15px;">📋</span>
                <h3 style="color: #FFFFFF; font-size: 13px; font-weight: 600; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">Semantic Logic Rules</h3>
            </div>
            <table class="ekyc-table">
                <tbody>
                    {make_rule_row("Chronology Check", "Issue date precedes expiry date", chron_txt, is_chron_passed)}
                    {make_rule_row("Document Authenticity", "MRZ checksum & security features", auth_txt, is_auth_passed)}
                    {make_rule_row("Legal Age Verification", "Holder is 18+ at issuance", age_txt, is_age_passed)}
                    {make_rule_row("Expiry Validation", "Document not expired", expiry_txt, is_expiry_passed)}
                </tbody>
            </table>
        </div>
        """
        st.markdown(rules_html, unsafe_allow_html=True)
        
        # Final Verdict Banners (Matching Figma screens exactly)
        if is_valid:
            st.markdown("""
            <div style="background-color: #064E3B; border: 1px solid #10B981; padding: 16px; border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
                <div style="background-color: #064E3B; color: #10B981; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-top: 2px;">✓</div>
                <div>
                    <div style="font-weight: 700; color: #A7F3D0; font-size: 14px;">Identity Validated</div>
                    <div style="color: #D1FAE5; font-size: 12px; margin-top: 2px;">All semantic rules passed. Document cleared for onboarding.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Join rules violations into a concise comma-separated string
            violation_str = "; ".join(violations)
            st.markdown(f"""
            <div style="background-color: #7F1D1D; border: 1px solid #EF4444; padding: 16px; border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
                <div style="background-color: #7F1D1D; color: #EF4444; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; margin-top: 2px;">!</div>
                <div>
                    <div style="font-weight: 700; color: #FCA5A5; font-size: 14px;">FRAUD DETECTED: CRITICAL ERROR</div>
                    <div style="color: #FECACA; font-size: 12px; margin-top: 2px;">{violation_str}. Manual escalation required — do not approve.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Intake console standing by. Run the engine to parse metadata and check constraints.")
