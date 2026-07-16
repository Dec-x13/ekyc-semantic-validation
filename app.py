import os
import datetime
import re
import json
import streamlit as st
from PIL import Image
from ocr_pipeline import run_ocr_pipeline
from rule_engine import validate_dates

# 1. Page Configuration (Standard Wide Layout)
st.set_page_config(
    page_title="eKYC Semantic Validation Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reference date for verification rules
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

# 2. Initialize Session State for State-Syncing
if 'input_source' not in st.session_state:
    st.session_state.input_source = "sample"
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = "id_0001.png"
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'active_file_path' not in st.session_state:
    st.session_state.active_file_path = os.path.join(IDS_DIR, "id_0001.png")
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

# 3. Sidebar Selection Panel
st.sidebar.title("📁 Document Selection")
st.sidebar.markdown("Manage identity documents for validation.")

input_mode = st.sidebar.radio(
    "Choose Input Method:",
    ["Select Sample ID from Dataset", "Upload Custom ID Image"]
)

# Get sample files
sample_files = []
if os.path.exists(IDS_DIR):
    sample_files = sorted([f for f in os.listdir(IDS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

if input_mode == "Select Sample ID from Dataset":
    if sample_files:
        selected_file = st.sidebar.selectbox("Choose Test File:", sample_files, index=sample_files.index(st.session_state.selected_file) if st.session_state.selected_file in sample_files else 0)
        
        # If selection changed, reset validation state to prevent stale data leaks
        if selected_file != st.session_state.selected_file or st.session_state.input_source != "sample":
            st.session_state.input_source = "sample"
            st.session_state.selected_file = selected_file
            st.session_state.active_file_path = os.path.join(IDS_DIR, selected_file)
            st.session_state.validated = False
            st.rerun()
            
        # Display Ground Truth reference metadata in sidebar
        if selected_file in metadata:
            st.sidebar.subheader("🏷️ Ground Truth metadata")
            st.sidebar.info(
                f"**Label:** {metadata[selected_file]['label']}\n\n"
                f"**Anomaly:** {metadata[selected_file]['flaw_type']}"
            )
    else:
        st.sidebar.warning("No sample files found. Run generator.py first.")
else:
    uploaded_file = st.sidebar.file_uploader("Upload ID Card Image:", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        if st.session_state.uploaded_file_name != uploaded_file.name or st.session_state.input_source != "upload":
            # Save file locally
            uploads_dir = os.path.join(BASE_DIR, "data", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            saved_path = os.path.join(uploads_dir, uploaded_file.name)
            with open(saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.session_state.input_source = "upload"
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.active_file_path = saved_path
            st.session_state.validated = False
            st.rerun()
    elif uploaded_file is None and st.session_state.input_source == "upload":
        # Reset to selected sample if file uploader is cleared
        st.session_state.input_source = "sample"
        st.session_state.active_file_path = os.path.join(IDS_DIR, st.session_state.selected_file)
        st.session_state.uploaded_file_name = None
        st.session_state.validated = False
        st.rerun()

# 4. Main Page Header
st.title("🛡️ Semantic Validation Approach for OCR Intake Systems")
st.markdown(
    "Detecting AI-generated synthetic identity documents (\"Frankenstein IDs\") "
    "using deterministic, white-box chronological logic gates."
)

# 5. Core Layout (Two Columns)
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📄 Document Preview")
    if os.path.exists(st.session_state.active_file_path):
        img = Image.open(st.session_state.active_file_path)
        st.image(img, caption="Intake Document Preview", use_container_width=True)
    else:
        st.info("Please select or upload a document to view its image.")

with col2:
    st.subheader("⚙️ Logical Validation Evaluation")
    
    run_btn = st.button("Run Semantic Validation Pipeline", use_container_width=True)
    
    if run_btn:
        with st.spinner("Processing image and running validation..."):
            # Execute pipeline on the exact active file path
            dob, issue, expiry, raw_text, is_sim = run_ocr_pipeline(st.session_state.active_file_path, metadata)
            is_valid, violations = validate_dates(dob, issue, expiry, REF_DATE)
            
            # Persist results in session state
            st.session_state.validated = True
            st.session_state.is_valid = is_valid
            st.session_state.violations = violations
            st.session_state.dob = dob
            st.session_state.issue = issue
            st.session_state.expiry = expiry
            st.session_state.raw_text = raw_text
            st.session_state.is_sim = is_sim
            st.rerun()

    # Render results if validation has been executed
    if st.session_state.validated:
        dob = st.session_state.dob
        issue = st.session_state.issue
        expiry = st.session_state.expiry
        raw_text = st.session_state.raw_text
        is_sim = st.session_state.is_sim
        is_valid = st.session_state.is_valid
        violations = st.session_state.violations
        
        # Parse names and ID numbers from text for display
        name_match = re.search(r'FULL\s+NAME:?\s*(.*)', raw_text, re.IGNORECASE)
        id_match = re.search(r'ID\s+NUMBER:?\s*(.*)', raw_text, re.IGNORECASE)
        card_name = name_match.group(1).strip() if name_match else "EXTRACT FAILED"
        card_id = id_match.group(1).strip() if id_match else "EXTRACT FAILED"
        
        # 1. Extracted Data metrics
        st.markdown("### 🔍 Extracted Data Metrics")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="Cardholder Name", value=card_name.title())
            st.metric(label="Date of Birth (DOB)", value=str(dob) if dob else "N/A")
        with m_col2:
            st.metric(label="ID Number", value=card_id)
            st.metric(label="Date of Issue", value=str(issue) if issue else "N/A")
            
        st.metric(label="Date of Expiry", value=str(expiry) if expiry else "N/A")
        st.markdown(f"*OCR Mode: {'Simulated Fallback (Tesseract missing)' if is_sim else 'Tesseract OCR Engine'}*")
        
        # 2. Logic Verification checks
        st.markdown("### 🔬 Logical Verification Checks")
        
        c1 = (dob and issue and issue >= dob)
        c2 = (issue and expiry and expiry > issue)
        
        if dob and issue:
            age_at_issue = issue.year - dob.year - ((issue.month, issue.day) < (dob.month, dob.day))
            c3 = (age_at_issue >= 18)
            c3_lbl = f"Legal Age Verification (Age at Issue: {age_at_issue} >= 18)"
        else:
            c3 = False
            c3_lbl = "Legal Age Verification (Age at Issue >= 18)"
            
        c4 = (expiry and expiry >= REF_DATE)
        
        if issue and expiry:
            max_exp = issue.replace(year=issue.year + 10) if not (issue.month == 2 and issue.day == 29) else datetime.date(issue.year + 10, 2, 28)
            c5 = (expiry <= max_exp)
        else:
            c5 = False
            
        st.markdown(f"* {'✅ **PASS**' if c1 else '❌ **FAIL**'} — Temporal Sequence: Issued After Birth (`Issue >= DOB`)")
        st.markdown(f"* {'✅ **PASS**' if c2 else '❌ **FAIL**'} — Temporal Sequence: Expiry After Issue (`Expiry > Issue`)")
        st.markdown(f"* {'✅ **PASS**' if c3 else '❌ **FAIL**'} — {c3_lbl}")
        st.markdown(f"* {'✅ **PASS**' if c4 else '❌ **FAIL**'} — Active Expiry Check (`Expiry >= {REF_DATE}`)")
        st.markdown(f"* {'✅ **PASS**' if c5 else '❌ **FAIL**'} — Policy Verification: Validity Duration <= 10 Years")
        
        # 3. Final Verdict Banner
        st.markdown("### 🏁 Final Decision Verdict")
        if is_valid:
            st.success(
                "**IDENTITY VALIDATED**\n\n"
                "All chronological sequence, legal age, and document validity checks passed successfully. "
                "No traces of AI generation logic forgery detected."
            )
        else:
            violations_list = "\n".join([f"* ⚠️ **[RULE VIOLATION]** {v}" for v in violations])
            st.error(
                "**FRAUD DETECTED / SUSPECT DOCUMENT**\n\n"
                "Semantic validation constraints violated. Traces of synthetic data generation anomalies found:\n\n"
                f"{violations_list}"
            )
    else:
        st.info("Intake console standing by. Click the button to run validation.")
