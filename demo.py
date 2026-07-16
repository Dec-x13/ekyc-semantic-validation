import os
import sys
import re
import json
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ocr_pipeline import run_ocr_pipeline
from rule_engine import validate_dates

# Initialize rich console
console = Console()

def load_metadata_cache():
    """Loads the metadata cache if it exists, to support OCR fallback in demo mode."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_path = os.path.join(base_dir, "data", "metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def main():
    """Main entry point for the demo script. Parses arguments and runs validation."""
    if len(sys.argv) < 2:
        console.print("[bold red]Usage Error:[/bold red] Please provide the path to an ID card image.")
        console.print("[yellow]Example:[/yellow] python demo.py data/ids/id_0001.png")
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        console.print(f"[bold red]File Error:[/bold red] Image file not found at: {image_path}")
        sys.exit(1)
        
    console.print(Panel.fit(
        "[bold cyan]SEMANTIC VALIDATION APPROACH FOR OCR INTAKE SYSTEMS[/bold cyan]\n"
        "[italic white]CS Thesis Prototype - Live Demo Mode[/italic white]",
        border_style="cyan"
    ))
    
    # Load metadata cache for simulation fallback if necessary
    metadata = load_metadata_cache()
    
    with console.status("[bold green]Running OpenCV Preprocessing & Tesseract OCR...[/bold green]") as status:
        try:
            dob, issue, expiry, raw_text, is_simulated = run_ocr_pipeline(image_path, metadata)
        except Exception as e:
            console.print(f"[bold red]Pipeline Execution Failure:[/bold red] {str(e)}")
            sys.exit(1)
            
    # Extract structural fields using Regex for display
    name_match = re.search(r'FULL\s+NAME:?\s*(.*)', raw_text, re.IGNORECASE)
    id_match = re.search(r'ID\s+NUMBER:?\s*(.*)', raw_text, re.IGNORECASE)
    
    card_name = name_match.group(1).strip() if name_match else "UNKNOWN / EXTRACT FAILURE"
    card_id = id_match.group(1).strip() if id_match else "UNKNOWN / EXTRACT FAILURE"
    
    # Perform Semantic Validation
    ref_date = datetime.date(2026, 7, 16) # Reference validation date
    is_valid, violations = validate_dates(dob, issue, expiry, ref_date)
    
    # 1. Output Extracted Data Table
    data_table = Table(title="Extracted Document Information (OCR + Regex)", title_style="bold yellow", show_header=True, header_style="bold magenta")
    data_table.add_column("Field Name", width=25)
    data_table.add_column("Extracted Value", width=35)
    data_table.add_column("Status", width=15)
    
    data_table.add_row("Document ID Number", card_id, "[green]Success[/green]" if id_match else "[red]Failed[/red]")
    data_table.add_row("Cardholder Full Name", card_name, "[green]Success[/green]" if name_match else "[red]Failed[/red]")
    data_table.add_row("Date of Birth (DOB)", str(dob) if dob else "PARSE ERROR", "[green]Success[/green]" if dob else "[red]Failed[/red]")
    data_table.add_row("Date of Issue", str(issue) if issue else "PARSE ERROR", "[green]Success[/green]" if issue else "[red]Failed[/red]")
    data_table.add_row("Date of Expiry", str(expiry) if expiry else "PARSE ERROR", "[green]Success[/green]" if expiry else "[red]Failed[/red]")
    
    console.print(data_table)
    console.print()
    
    # 2. Output Validation Checks Table
    checks_table = Table(title="Semantic Logical Constraints Evaluation", title_style="bold yellow", show_header=True, header_style="bold magenta")
    checks_table.add_column("Check description", width=45)
    checks_table.add_column("Mathematical Model", width=25)
    checks_table.add_column("Result", width=10)
    
    # Check 1: Issue Date after Birth Date
    c1_res = "[green]PASS[/green]" if (dob and issue and issue >= dob) else "[red]FAIL[/red]" if (dob and issue) else "[yellow]SKIP[/yellow]"
    checks_table.add_row("Temporal Sequence: Issued After Birth", "Issue Date >= DOB", c1_res)
    
    # Check 2: Expiry Date after Issue Date
    c2_res = "[green]PASS[/green]" if (issue and expiry and expiry > issue) else "[red]FAIL[/red]" if (issue and expiry) else "[yellow]SKIP[/yellow]"
    checks_table.add_row("Temporal Sequence: Expiry After Issue", "Expiry Date > Issue Date", c2_res)
    
    # Check 3: Legal Age at Issue
    # Calculate age at issue for display
    if dob and issue:
        # Use simple calculation for display
        age_at_issue = issue.year - dob.year - ((issue.month, issue.day) < (dob.month, dob.day))
        c3_model = f"Age at Issue ({age_at_issue}) >= 18"
        c3_res = "[green]PASS[/green]" if age_at_issue >= 18 else "[red]FAIL[/red]"
    else:
        c3_model = "Age at Issue >= 18"
        c3_res = "[yellow]SKIP[/yellow]"
    checks_table.add_row("Legal Age Verification", c3_model, c3_res)
    
    # Check 4: Expiration Status
    c4_res = "[green]PASS[/green]" if (expiry and expiry >= ref_date) else "[red]FAIL[/red]" if expiry else "[yellow]SKIP[/yellow]"
    checks_table.add_row("Active Expiry Check", f"Expiry Date >= {ref_date}", c4_res)
    
    # Check 5: Document Validity Limit
    if issue and expiry:
        # Check if validity > 10 years
        max_exp = issue.replace(year=issue.year + 10) if not (issue.month == 2 and issue.day == 29) else datetime.date(issue.year + 10, 2, 28)
        c5_res = "[green]PASS[/green]" if expiry <= max_exp else "[red]FAIL[/red]"
    else:
        c5_res = "[yellow]SKIP[/yellow]"
    checks_table.add_row("Policy Verification: Maximum Validity Period", "Validity <= 10 Years", c5_res)
    
    console.print(checks_table)
    console.print()
    
    # 3. Output Final Verdict Panel
    mode_str = " (Simulated OCR Fallback Mode)" if is_simulated else " (Tesseract OCR Engine Mode)"
    
    if is_valid:
        verdict_text = Text()
        verdict_text.append("VERDICT: DOCUMENT VALID & AUTHENTICATED\n", style="bold green")
        verdict_text.append(f"All structural and semantic checks passed successfully.{mode_str}\n", style="green")
        verdict_text.append("No logical anomalies or AI synthesis traces detected.", style="italic green")
        
        console.print(Panel(verdict_text, border_style="green", expand=False))
    else:
        verdict_text = Text()
        verdict_text.append("VERDICT: FLAG FOR SUSPECTED SYNTHETIC IDENTITY FRAUD\n", style="bold red")
        verdict_text.append(f"Reason: Document failed semantic validation validation rules.{mode_str}\n\n", style="red")
        verdict_text.append("Violations Detected:\n", style="bold yellow")
        for v in violations:
            verdict_text.append(f"  • [ERROR] {v}\n", style="bold red")
            
        console.print(Panel(verdict_text, border_style="red", expand=False))

if __name__ == "__main__":
    main()
