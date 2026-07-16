import sys
import generator
import evaluate

def main():
    print("======================================================================")
    print(" SEMANTIC VALIDATION FOR OCR INTAKE SYSTEMS: END-TO-END PIPELINE")
    print("======================================================================")
    
    # Run Component 1: Dataset Generation (Generates 1,000 digital ID card images)
    print("\n--- STEP 1: Dataset Generation ---")
    generator.main()
    
    # Run Component 4: Evaluation and Metrics (OCR pipeline, Rule engine validation, and comparison)
    print("\n--- STEP 2: OCR Extraction, Rule Validation, and Evaluation ---")
    evaluate.main()
    
    print("======================================================================")
    print(" Pipeline Execution Completed Successfully!")
    print("======================================================================")

if __name__ == "__main__":
    main()
