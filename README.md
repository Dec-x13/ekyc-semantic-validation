# SentinelKYC: Semantic Validation Approach for OCR Intake Systems
## CS Thesis Capstone Project — Final Defense Implementation

SentinelKYC implements a **Semantic Validation Approach for OCR Intake Systems** to intercept and flag AI-generated synthetic identity fraud ("Frankenstein IDs") during digital onboarding. 

While modern generative models can yield "visually perfect" forged document scans that pass traditional pixel-forensic checks and standard OCR transcriptions, they lack logical context. SentinelKYC acts as a deterministic, "white-box" semantic logic gate directly following standard OCR, extracting and evaluating dates and Machine Readable Zones (MRZ) against physical, chronological, and policy rules.

---

## 1. Project Directory Structure

```
capstone_project/
├── data/
│   ├── ids/                  # Generated 1,000 hyper-realistic synthetic digital ID images (500 Valid, 500 Frankenstein)
│   ├── real_ids/             # Directory where uploaded real-world ID card scans are saved
│   ├── uploads/              # Temp directory storing uploaded images during live operations
│   └── metadata.json         # Ground truth catalog for evaluation and simulated OCR fallback
├── generator.py              # Component 1: Hyper-Realistic Synthetic ID Generator
├── ocr_pipeline.py           # Component 2: OpenCV Image Preprocessing & pytesseract OCR Pipeline
├── rule_engine.py            # Component 3: White-Box Semantic Logic Validation Engine
├── evaluate.py               # Component 4: Confusion Matrix & Classification Metrics Calculator
├── demo.py                   # Component 5: Interactive Terminal Presentation CLI Tool
├── app.py                    # Component 6: Callback-Driven SentinelKYC Web Console (Streamlit)
├── main.py                   # Orchestrator running the end-to-end evaluation pipeline
├── requirements.txt          # Library dependencies index
└── README.md                 # Project README and Capstone Audit Documentation
```

---

## 2. Technical Stack & Dependencies
*   **Streamlit (v1.26.0+):** Dashboard framework rebuilt using a callback-driven session state model.
*   **OpenCV (cv2):** Image grayscaling to optimize contrast for text recognition.
*   **Pillow (PIL):** High-fidelity programmatic text, signature, holographic ghost overlays, and printing structures rendering.
*   **pytesseract (Tesseract OCR):** Text character transcription engine.
*   **python-dateutil:** For leap-year-safe calendar-based date math (`relativedelta`).
*   **Faker:** Realistic biometric mock profile details generator.
*   **Rich:** CLI panels, colors, and layout tables compiler.

---

## 3. Modular Implementation Summaries

### A. Hyper-Realistic Synthetic Generator (`generator.py`)
Generates 1,000 synthetic digital IDs (50% Valid, 50% Frankenstein). Replicates physical security artifacts and camera scan imperfections:
*   *Printed Halftone Dot Simulation:* Downscales the biometric silhouette to $34 \times 36$ pixels via `Image.NEAREST` and scales it back up, blending it at 35% opacity to replicate halftone dot structures.
*   *Ghost Image Hologram:* Pastes a 25%-opacity, blurred grayscale duplicate silhouette in the bottom-right corner.
*   *Organic Handwriting Overlay:* Dynamic cursive script font generation in dark blue ink (`#1D4ED8`) with random rotation skews ($\pm 2^{\circ}$ to $6^{\circ}$).
*   *Machine Readable Zone (MRZ):* Appends ICAO Document 9303 compliant 3-line monospaced blocks (consisting of name, DOB, issuing country, and ID number).
*   *Photographic Scanning Artifacts:* Adds Gaussian noise grain via NumPy, applies random card skews ($\pm 0.5^{\circ}$), and overlays camera lens focus blur.

### B. White-Box Semantic Logic Engine (`rule_engine.py`)
Validates date relationships using calendar relativedelta shifts to handle leap years (e.g. Feb 29 + 10 years maps correctly to Feb 28):
1.  *Temporal Sequence Check:* DOB $\le$ Issue Date $<$ Expiry Date.
2.  *Legal Age Limit:* Age at issue $\ge$ 18.
3.  *Expiration Status:* Expiry Date $\ge$ Reference Date (July 16, 2026).
4.  *Validity Duration limit:* Expiry Date $\le$ Issue Date + 10 years.

### C. Callback-Driven Web Dashboard (`app.py`)
Features the SentinelKYC dark-themed dashboard console:
*   *Callbacks & State Synchronization:* Manages dropdowns, generators, and uploader events strictly via callback parameters (`on_change` / `on_click`), binding variables to state objects (`active_doc_path`, `uploaded_file_obj`, `doc_source`) before the UI renders to eliminate Streamlit state loss.
*   *Synthetic Generator Module:* Sidebar button triggers `generator.py` logic, automatically saving and selecting a new ID card formatted as: `[LIVE GEN] {ID_NUMBER}-{V or F} • National ID • Synthesia`.
*   *Search Filter:* Sidebar search input filters the test document dropdown options in real-time.
*   *Upload & Save Real IDs:* Safe file saving from the uploader to `data/real_ids/` directory, mapped in a separate state path to prevent UI selection conflicts.
*   *Flagged UI Indicators:* Dynamically appends red `<span class="flagged-pill">FLAGGED</span>` labels to anomalous table fields.

---

## 4. Robust Validation & Parsing Fallbacks

### A. Missing Machine Readable Zones (MRZ)
Real-world driver's licenses often lack MRZ lines. [ocr_pipeline.py](file:///C:/Users/Admin/Documents/MyProjects/capstone_project/ocr_pipeline.py) exposes a safe helper `extract_mrz(text)` that isolates 30-char monospaced formats. If missing, it returns `None` rather than raising `IndexError` or `NoneType` faults. [app.py](file:///C:/Users/Admin/Documents/MyProjects/capstone_project/app.py) handles `mrz = None` safely by updating the logic list status to `"MRZ Not Found"` instead of throwing an app crash.

### B. Garbage OCR Text Dates
If the OCR reads unreadable character garbage, [rule_engine.py](file:///C:/Users/Admin/Documents/MyProjects/capstone_project/rule_engine.py) catches `TypeError` and `ValueError` comparisons inside `try/except` wrappers. Rather than crashing the pipeline, it appends a `"Data Unreadable"` status indicator to the specific rule violations.

### C. Top-Level UI Verification Safety
In [app.py](file:///C:/Users/Admin/Documents/MyProjects/capstone_project/app.py), the main OCR pipeline validation is wrapped in a top-level try/except block. If a corrupted image or unreadable document format is uploaded, it captures the crash and displays a custom warning alert: `🚨 Verification Failed: Unrecognized Document Format or Unreadable Data`.

---

## 5. Classification Performance Evaluation

Evaluated against the generated dataset of 1,000 synthetic digital IDs using the reference validation date **July 16, 2026**.

*   **State 1 (Baseline standard OCR):** Transcribes text and assumes it is valid.
*   **State 2 (Rule-Enhanced OCR):** Parses dates and validates them against the engine.

### Classification Performance Results

| Metric | State 1 (Baseline OCR) | State 2 (Rule-Enhanced OCR) | Security Improvement |
| :--- | :---: | :---: | :---: |
| **True Positives (TP)** *(Correctly Flagged Forgeries)* | 0 | 500 | **+500** |
| **True Negatives (TN)** *(Correctly Cleared Valid IDs)* | 500 | 500 | **0 (Leap Year bugs resolved)** |
| **False Positives (FP)** *(Legitimate IDs Incorrectly Flagged)* | 0 | 0 | **0 (0.00% FP rate)** |
| **False Negatives (FN)** *(Missed Forgeries)* | 500 | 0 | **-500 (No fraud missed)** |
| **Recall (Detection Rate)** | 0.00% | 100.00% | **+100.00%** |
| **F1-Score** | 0.00% | 100.00% | **+100.00%** |
| **Accuracy** | 50.00% | 100.00% | **+50.00%** |

*Note: Resolving leap-year drift using `dateutil.relativedelta` cleared the 2 False Positives, reaching a perfect 100.00% F1-score.*

---

## 6. Execution Guidelines

### 1. Library Installation
Ensure you have the required Python libraries installed:
```bash
pip install opencv-python pytesseract Faker pillow python-dateutil rich streamlit
```
*Note: To execute real OCR text extraction, you must install the **Tesseract OCR binary** on your machine and ensure it is in your system PATH. If Tesseract is not installed, the pipeline automatically activates its metadata-driven simulation mode.*

### 2. Run End-to-End Orchestrator Pipeline
To run dataset generation and print State 1 vs. State 2 classification metrics:
```bash
python main.py
```

### 3. Run Streamlit Web Application
To launch the dark-themed SentinelKYC Verification Console:
```bash
python -m streamlit run app.py
```

### 4. Run Terminal Live Presentation CLI
To demonstrate validation checks for a single ID image in color-coded rich panels:
```bash
python demo.py data/ids/id_0001.png
```
