import datetime
from dateutil.relativedelta import relativedelta

def validate_dates(dob, issue_date, expiry_date, reference_date=None):
    """
    Validates identity document dates and flags chronological or legal anomalies.
    
    This function acts as a deterministic, "white-box" semantic logic gate to identify 
    synthetic identity documents ("Frankenstein IDs"). It checks dates against rules 
    representing physical and legal constraints.

    Parameters:
    ----------
    dob : datetime.date or None
        The parsed Date of Birth of the cardholder.
    issue_date : datetime.date or None
        The parsed Date of Issue of the identity document.
    expiry_date : datetime.date or None
        The parsed Date of Expiry of the identity document.
    reference_date : datetime.date, optional
        The validation date to check expiration against. Defaults to 2026-07-16.

    Returns:
    -------
    is_valid : bool
        True if all semantic checks pass, False if any violation is triggered.
    violations : list of str
        A list of human-readable, explainable rule violation messages.
    """
    violations = []
    
    # 1. Reference Date Initialization
    # Establish the reference system validation date (defaults to the digital intake checkpoint date).
    if reference_date is None:
        reference_date = datetime.date(2026, 7, 16)
        
    # 2. Structural Parsing Checks
    # Verify that all mandatory date fields were successfully extracted by the OCR pipeline.
    if dob is None:
        violations.append("Date of Birth field could not be parsed or is missing")
    if issue_date is None:
        violations.append("Issue Date field could not be parsed or is missing")
    if expiry_date is None:
        violations.append("Expiry Date field could not be parsed or is missing")
        
    if violations:
        return False, violations
        
    # 3. Temporal Sequence Validation (Physical Chronology)
    # Proof: A document cannot be issued before the cardholder is born.
    # Mathematical expression: Issue Date >= DOB
    if issue_date < dob:
        violations.append("Temporal sequence violation: Issue Date is before Date of Birth")
        
    # Proof: A document's expiration date must be strictly after its issue date.
    # Mathematical expression: Expiry Date > Issue Date
    if expiry_date <= issue_date:
        violations.append("Temporal sequence violation: Expiry Date is on or before Issue Date")
        
    # 4. Legal Age Verification
    # Proof: The cardholder must satisfy the legal age requirement at the time of document issue.
    # We use dateutil.relativedelta to calculate the exact calendar age, which handles leap years
    # flawlessly (including Feb 29 birthdates mapping to Feb 28 in non-leap years).
    # Mathematical expression: Age at Issue = relativedelta(Issue Date, DOB).years >= 18
    age_at_issue = relativedelta(issue_date, dob).years
    if age_at_issue < 18:
        violations.append(
            f"Age requirement mathematically violated: Person was only {age_at_issue} "
            f"years old at the time of issue (minimum 18 required)"
        )
        
    # 5. Expiration Status Check
    # Proof: An identity document submitted for intake must be current and not expired.
    # Mathematical expression: Expiry Date >= Reference Date
    if expiry_date < reference_date:
        violations.append(
            f"Expiry date in the past: Document expired on {expiry_date.strftime('%Y-%m-%d')} "
            f"(reference date is {reference_date.strftime('%Y-%m-%d')})"
        )
        
    # 6. Validity Period Check (Optional Policy Rule)
    # Proof: Standard digital ID cards are issued for a maximum validity period of 10 years.
    # Mathematical expression: Expiry Date <= Issue Date + 10 calendar years
    max_expiry_date = issue_date + relativedelta(years=10)
    if expiry_date > max_expiry_date:
        violations.append(
            f"Validity duration anomaly: Document validity period exceeds maximum limit of 10 years "
            f"(Expiry: {expiry_date.strftime('%Y-%m-%d')}, Max Allowed Expiry: {max_expiry_date.strftime('%Y-%m-%d')})"
        )
        
    is_valid = len(violations) == 0
    return is_valid, violations
