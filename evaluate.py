import os
import json
import datetime
from ocr_pipeline import run_ocr_pipeline
from rule_engine import validate_dates

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(BASE_DIR, "data", "metadata.json")
IDS_DIR = os.path.join(BASE_DIR, "data", "ids")
REF_DATE = datetime.date(2026, 7, 16) # Reference validation date

def calculate_metrics(y_true, y_pred):
    """
    Calculates confusion matrix and classification performance metrics.

    Sets "Fraudulent / Frankenstein ID" as the Positive Class (1)
    and "Legitimate / Valid ID" as the Negative Class (0).

    Parameters:
    ----------
    y_true : list of int
        The ground truth binary labels (1 for Frankenstein, 0 for Valid).
    y_pred : list of int
        The predicted binary labels (1 for Frankenstein, 0 for Valid).

    Returns:
    -------
    dict
        A dictionary containing the calculated metrics:
        - "confusion_matrix": dict of TP, TN, FP, FN counts.
        - "precision": float
        - "recall": float
        - "f1_score": float
        - "accuracy": float
    """
    tp = 0 # Frankenstein ID correctly flagged as Fraudulent
    tn = 0 # Valid ID correctly accepted as Valid
    fp = 0 # Valid ID incorrectly flagged as Fraudulent
    fn = 0 # Frankenstein ID incorrectly accepted as Valid
    
    for true, pred in zip(y_true, y_pred):
        if true == 1 and pred == 1:
            tp += 1
        elif true == 0 and pred == 0:
            tn += 1
        elif true == 0 and pred == 1:
            fp += 1
        elif true == 1 and pred == 0:
            fn += 1
            
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0
    
    return {
        "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy
    }

def print_metrics(state_name, metrics):
    """
    Formats and prints the confusion matrix and performance metrics to the console.

    Parameters:
    ----------
    state_name : str
        The name of the evaluation state (e.g. State 1, State 2).
    metrics : dict
        The performance metrics dictionary computed by calculate_metrics().
    """
    cm = metrics["confusion_matrix"]
    print(f"\n==========================================")
    print(f" METRICS FOR: {state_name}")
    print(f"==========================================")
    print(f"Confusion Matrix:")
    print(f"  - True Positives (TP - Flagged Fraud):     {cm['TP']}")
    print(f"  - True Negatives (TN - Accepted Valid):    {cm['TN']}")
    print(f"  - False Positives (FP - Flagged Valid):    {cm['FP']}")
    print(f"  - False Negatives (FN - Missed Fraud):     {cm['FN']}")
    print(f"Performance Metrics:")
    print(f"  - Accuracy:  {metrics['accuracy'] * 100:.2f}%")
    print(f"  - Precision: {metrics['precision'] * 100:.2f}%")
    print(f"  - Recall:    {metrics['recall'] * 100:.2f}%")
    print(f"  - F1-Score:  {metrics['f1_score'] * 100:.2f}%")

def main():
    """
    Orchestrates the evaluation pipeline across the generated dataset of 1,000 documents.

    Loads the dataset ground truth catalog from metadata.json, runs each image 
    through the OCR extraction and Regex parsing, validates extracted fields 
    using the Semantic Logic Engine, and prints a comparative classification report 
    comparing Baseline OCR (State 1) vs. Rule-Enhanced OCR (State 2).
    """
    if not os.path.exists(METADATA_PATH):
        print(f"Error: Metadata file not found at {METADATA_PATH}.")
        print("Please run generator.py first to create the dataset.")
        return
        
    print("Loading metadata...")
    with open(METADATA_PATH, "r") as f:
        metadata = json.load(f)
        
    y_true = []       # Ground truth: 1 for Frankenstein, 0 for Valid
    y_pred_state1 = [] # State 1: Baseline OCR (assumes everything is valid/0)
    y_pred_state2 = [] # State 2: Rule-Enhanced OCR (1 if flagged as fraudulent, 0 otherwise)
    
    print("\nRunning evaluation on 1,000 synthetic digital IDs...")
    print("This runs the OCR pipeline and validation checks for each image...")
    
    ocr_simulated_count = 0
    ocr_real_count = 0
    
    # Process each ID card
    count = 0
    for filename, ground_truth in metadata.items():
        image_path = os.path.join(IDS_DIR, filename)
        
        # Determine ground truth (1 if Frankenstein, 0 if Valid)
        true_label = 1 if ground_truth["label"] == "Frankenstein" else 0
        y_true.append(true_label)
        
        # 1. State 1 (Baseline standard OCR)
        # Simply assumes extracted text is valid and accepts the ID (predicted 0)
        y_pred_state1.append(0)
        
        # 2. Run OCR Pipeline to parse dates
        # Pass metadata cache to allow simulation fallback if Tesseract is missing
        dob, issue, expiry, raw_text, is_sim = run_ocr_pipeline(image_path, metadata)
        
        if is_sim:
            ocr_simulated_count += 1
        else:
            ocr_real_count += 1
            
        # 3. State 2 (Rule-Enhanced OCR)
        # Run Semantic validation engine
        is_valid, violations = validate_dates(dob, issue, expiry, REF_DATE)
        
        # If not valid, we predict Fraudulent (1), otherwise Valid (0)
        pred_label = 0 if is_valid else 1
        y_pred_state2.append(pred_label)
        
        count += 1
        if count % 100 == 0:
            print(f"Processed {count}/1000 document images...")
            
    print("\nProcessing complete!")
    print(f"OCR Execution Mode: {ocr_real_count} real OCR calls, {ocr_simulated_count} simulated OCR fallbacks.")
    
    # Calculate metrics
    metrics_state1 = calculate_metrics(y_true, y_pred_state1)
    metrics_state2 = calculate_metrics(y_true, y_pred_state2)
    
    # Output metrics
    print_metrics("State 1 - Standard Baseline OCR (No Rules)", metrics_state1)
    print_metrics("State 2 - Rule-Enhanced OCR Pipeline", metrics_state2)
    
    # Security Improvement Summary
    print(f"\n==========================================")
    print(f" SECURITY IMPROVEMENT SUMMARY")
    print(f"==========================================")
    recall_improvement = (metrics_state2["recall"] - metrics_state1["recall"]) * 100
    f1_improvement = (metrics_state2["f1_score"] - metrics_state1["f1_score"]) * 100
    accuracy_improvement = (metrics_state2["accuracy"] - metrics_state1["accuracy"]) * 100
    
    print(f"Security Detection Recall Improvement:  +{recall_improvement:.2f}% (from {metrics_state1['recall']*100:.1f}% to {metrics_state2['recall']*100:.1f}%)")
    print(f"Overall Classification F1-Score Gain:   +{f1_improvement:.2f}% (from {metrics_state1['f1_score']*100:.1f}% to {metrics_state2['f1_score']*100:.1f}%)")
    print(f"Overall Classification Accuracy Gain:   +{accuracy_improvement:.2f}% (from {metrics_state1['accuracy']*100:.1f}% to {metrics_state2['accuracy']*100:.1f}%)")
    print("==========================================\n")

if __name__ == "__main__":
    main()
