# Detecting Logical Synthesis in Digital Onboarding: A Semantic Validation Approach

This project implements a **Semantic Validation Approach for OCR Intake Systems** to detect AI-generated synthetic identity documents ("Frankenstein IDs"). 

Traditional identity validation pipelines rely on visual forensics (detecting pixel manipulation) or standard OCR. However, generative AI can produce visually perfect identity documents that easily bypass these defenses. This system acts as a "White-Box" semantic logic gate, parsing extracted texts using regular expressions and checking them for real-world consistency (temporal sequences and legal age limits).

---

## Project Directory Structure
```
capstone_project/
├── data/
│   ├── ids/                  # Generated 1,000 digital ID card images
│   └── metadata.json         # Ground truth metadata for evaluation and simulation fallback
├── generator.py              # Component 1: Synthetic Dataset Generator
├── ocr_pipeline.py           # Component 2: Grayscaling and Text Extraction Pipeline
├── rule_engine.py            # Component 3: White-Box Semantic Logic Engine
├── evaluate.py               # Component 4: Confusion Matrix and Performance Metric Calculator
├── main.py                   # Orchestrator to run the entire pipeline end-to-end
└── README.md                 # Project documentation and summary
```

---

## Tech Stack
*   **Python 3**
*   **OpenCV (cv2):** For loading, manipulating, and grayscaling images to improve text contrast.
*   **Pillow (PIL):** To programmatically render high-quality text onto digital ID templates.
*   **pytesseract (Tesseract OCR):** For reading textual fields from document images.
*   **Faker:** For generating realistic names, ID numbers, and address details.
*   **Regex (re):** For extracting date patterns and mapping them to structured `datetime.date` objects.

---

## How to Run

### 1. Requirements Setup
Ensure you have the required Python libraries installed:
```bash
pip install opencv-python pytesseract Faker pillow scikit-learn
```

> [!NOTE]
> To execute real OCR text extraction, you must install the **Tesseract OCR engine** on your machine and ensure it is in your system PATH. If Tesseract is not installed, the pipeline will automatically fall back to a metadata-driven simulation mode, allowing the entire pipeline and evaluation to remain fully runnable.

### 2. Run the End-to-End Pipeline
To generate the 1,000 synthetic digital IDs, execute OCR extraction, run validation rules, and output performance metrics, simply run:
```bash
python main.py
```

You can also run the components individually:
*   **Generate Dataset:** `python generator.py`
*   **Evaluate System:** `python evaluate.py`

---

## Performance Summary

The system evaluates two states:
*   **State 1 (Baseline standard OCR):** Transcribes text and assumes it is valid.
*   **State 2 (Rule-Enhanced OCR):** Parses dates and validates them against rules:
    1.  *Temporal Sequence:* $\text{Date of Birth} \le \text{Issue Date} < \text{Expiry Date}$
    2.  *Legal Age Limit:* $\text{Age at Issue} \ge 18$
    3.  *Expiration Status:* $\text{Expiry Date} \ge \text{Reference Date (2026-07-16)}$

### Classification Performance Results

| Metric | State 1 (Baseline standard OCR) | State 2 (Rule-Enhanced OCR) | Security Improvement |
| :--- | :---: | :---: | :---: |
| **True Positives (TP)** | 0 | 500 | **+500** |
| **True Negatives (TN)** | 500 | 498 | **-2 (Due to leap years)** |
| **False Positives (FP)** | 0 | 2 | **+2** |
| **False Negatives (FN)** | 500 | 0 | **-500 (No fraud missed)** |
| **Recall (Detection Rate)** | 0.00% | 100.00% | **+100.00%** |
| **F1-Score** | 0.00% | 99.80% | **+99.80%** |
| **Accuracy** | 50.00% | 99.80% | **+49.80%** |

### Key Findings
Standard OCR has a **semantic blind spot** and completely fails to detect synthetic documents (0% detection rate). The **Rule-Enhanced OCR Pipeline** achieved a **100% Detection Recall Rate** (+100.00% gain) by checking internal consistency, blocking all 500 synthetic documents with chronological or underage logical flaws.
