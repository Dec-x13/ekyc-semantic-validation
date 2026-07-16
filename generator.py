import os
import json
import random
import datetime
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dateutil.relativedelta import relativedelta
from faker import Faker

# Initialize Faker
fake = Faker('en_US')

# Constants
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ids")
METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "metadata.json")
REF_DATE = datetime.date(2026, 7, 16) # Reference validation date

# Bounding box layout (left, top, right, bottom) for OCR extraction testing
LAYOUT = {
    "id_number": (240, 95, 550, 125),
    "full_name": (240, 135, 550, 165),
    "dob": (240, 175, 550, 205),
    "issue_date": (240, 215, 550, 245),
    "expiry_date": (240, 255, 550, 285)
}

def get_font(size, bold=False):
    """
    Loads a standard system sans-serif font (Arial, Calibri, Tahoma, Segoe UI).
    Falls back to default if unavailable.
    """
    font_names = ["arial.ttf", "calibri.ttf", "tahoma.ttf", "segoeui.ttf"]
    if bold:
        font_names = ["arialbd.ttf", "calibrib.ttf", "tahomabd.ttf", "segoeuiib.ttf"]
        
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            pass
            
    # Try Windows absolute paths
    win_font_paths = [f"C:\\Windows\\Fonts\\{name}" for name in font_names]
    for path in win_font_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            pass
            
    return ImageFont.load_default()

def get_mono_font(size):
    """Loads a monospace system font (Consolas, Courier New) for MRZ rendering."""
    font_names = ["consola.ttf", "cour.ttf", "lucon.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            pass
    win_paths = [f"C:\\Windows\\Fonts\\{name}" for name in font_names]
    for path in win_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            pass
    return ImageFont.load_default()

def get_handwriting_font(size):
    """Loads a script/cursive system font for signature simulation."""
    font_names = ["Edwardian Script ITC.ttf", "Segoe Script.ttf", "Gabriola.ttf", "Lucida Handwriting.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            pass
    win_paths = [f"C:\\Windows\\Fonts\\{name}" for name in font_names]
    for path in win_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            pass
    return ImageFont.load_default()

def create_portrait(name):
    """
    Generates a realistic silhouette portrait representing the cardholder.
    Applies pixelation resizing and blending to simulate printed plastic halftones.
    """
    # Create portrait canvas
    portrait = Image.new("RGB", (170, 180), "#D0D8E5")
    draw = ImageDraw.Draw(portrait)
    
    # Render basic biometric silhouette
    # Head outline
    draw.ellipse([(60, 25), (110, 75)], fill="#7A8D9F", outline="#506070", width=1)
    # Shoulders
    draw.chord([(25, 85), (145, 175)], start=180, end=360, fill="#7A8D9F", outline="#506070", width=1)
    
    # Apply halftone/print pixelation pattern by scaling down and up
    portrait_small = portrait.resize((34, 36), Image.NEAREST)
    portrait_pixelated = portrait_small.resize((170, 180), Image.NEAREST)
    
    # Blend to simulate subtle physical printing dot structures
    printed_portrait = Image.blend(portrait, portrait_pixelated, alpha=0.35)
    return printed_portrait

def create_ghost_image(portrait):
    """
    Creates a holographic 'ghost image' standard on security documents.
    Blurs the silhouette and scales opacity to 25%.
    """
    # Convert to grayscale to simulate laser engraving
    ghost = portrait.convert("L").convert("RGB").convert("RGBA")
    
    # Scale alpha opacity
    pixels = ghost.getdata()
    alpha_adjusted_pixels = []
    for r, g, b, a in pixels:
        alpha_adjusted_pixels.append((r, g, b, int(a * 0.25)))
    ghost.putdata(alpha_adjusted_pixels)
    
    # Apply slight holographic blur
    ghost = ghost.filter(ImageFilter.GaussianBlur(1.5))
    return ghost

def create_signature_stamp(name):
    """Generates an organic handwritten signature in blue ink rotated slightly."""
    # Translucent signature canvas
    sig_img = Image.new("RGBA", (170, 30), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sig_img)
    
    font = get_handwriting_font(18)
    sig_text = f"{name.split()[0]} {name.split()[-1]}"
    
    # Draw in dark blue ink
    draw.text((10, 2), sig_text, fill="#1D4ED8", font=font)
    
    # Rotate signature slightly
    sig_img = sig_img.rotate(random.uniform(-6.0, -2.0), resample=Image.BICUBIC, expand=False)
    return sig_img

def generate_mrz_lines(id_num, name, dob):
    """Generates a standard 3-line MRZ zone using parsed document data."""
    parts = name.upper().replace(".", "").replace(",", "").split()
    first_name = parts[0] if len(parts) > 0 else "JOHN"
    last_name = parts[-1] if len(parts) > 1 else "DOE"
    
    last_cleaned = re.sub(r'[^A-Z]', '', last_name)
    first_cleaned = re.sub(r'[^A-Z]', '', first_name)
    
    # Line 1: Type, Issuing Country, ID Number
    line1 = f"I<SYN{id_num}<<<<<<<<<<<<<<<"[:30].ljust(30, "<")
    # Line 2: DOB in YYMMDD
    dob_mrz = dob.strftime("%y%m%d")
    line2 = f"{dob_mrz}<<<<<<<<<<<<<<<<<<<<<<"[:30].ljust(30, "<")
    # Line 3: Name
    line3 = f"{last_cleaned}<<{first_cleaned}<<<<<<<<<<<<<<<<"[:30].ljust(30, "<")
    
    return [line1, line2, line3]

def draw_id_card(id_num, name, dob, issue_date, expiry_date):
    """
    Assembles a hyper-realistic digital identity card.
    Incorporates pixelated portraits, handwriting overlays, holographic ghost images,
    an MRZ zone, and post-assembly scanning artifacts (noise, rotation, and blur).
    """
    # Slightly taller canvas to hold MRZ zone (600x380)
    card = Image.new("RGB", (600, 380), "#F1F5F9")
    draw = ImageDraw.Draw(card)
    
    # 1. Background Security Guilloche lines simulation
    for x in range(-380, 600, 25):
        draw.line([(x, 0), (x + 380, 380)], fill="#E2E8F0", width=1)
        
    # 2. Card Boundary
    draw.rectangle([(5, 5), (595, 375)], outline="#1E293B", width=3)
    
    # 3. Header Band
    draw.rectangle([(8, 8), (592, 70)], fill="#1E293B")
    title_font = get_font(22, bold=True)
    subtitle_font = get_font(11, bold=False)
    draw.text((20, 15), "REPUBLIC OF SYNTHESIA", fill="#FFFFFF", font=title_font)
    draw.text((20, 42), "NATIONAL DIGITAL ONBOARDING IDENTITY CARD", fill="#38BDF8", font=subtitle_font)
    
    # 4. Paste Biometric Portrait
    portrait = create_portrait(name)
    card.paste(portrait, (25, 95))
    draw.rectangle([(24, 94), (196, 276)], outline="#1E293B", width=2)
    
    # 5. Overlay Signature
    sig = create_signature_stamp(name)
    card.paste(sig, (25, 290), sig)
    
    # 6. Laser Hologram Ghost Image (Bottom Right)
    ghost = create_ghost_image(portrait)
    # Resize slightly smaller
    ghost_small = ghost.resize((85, 90), Image.BICUBIC)
    card.paste(ghost_small, (490, 185), ghost_small)
    
    # 7. Metadata Fields rendering
    text_font = get_font(14, bold=True)
    label_font = get_font(10)
    
    fields = [
        ("ID NUMBER", f"ID-{id_num}", LAYOUT["id_number"]),
        ("FULL NAME", name.upper(), LAYOUT["full_name"]),
        ("DATE OF BIRTH", dob.strftime("%Y-%m-%d"), LAYOUT["dob"]),
        ("ISSUE DATE", issue_date.strftime("%Y-%m-%d"), LAYOUT["issue_date"]),
        ("EXPIRY DATE", expiry_date.strftime("%Y-%m-%d"), LAYOUT["expiry_date"])
    ]
    
    for label, val, bbox in fields:
        draw.text((bbox[0], bbox[1] - 15), label, fill="#475569", font=label_font)
        draw.text((bbox[0], bbox[1]), val, fill="#0F172A", font=text_font)
        
    # 8. Render MRZ Band at the Bottom
    draw.rectangle([(8, 325), (592, 372)], fill="#E2E8F0")
    mrz_lines = generate_mrz_lines(id_num, name, dob)
    mrz_font = get_mono_font(11)
    
    draw.text((25, 328), mrz_lines[0], fill="#0F172A", font=mrz_font)
    draw.text((25, 342), mrz_lines[1], fill="#0F172A", font=mrz_font)
    draw.text((25, 356), mrz_lines[2], fill="#0F172A", font=mrz_font)
    
    # 9. Apply Scanning Artifact: Gaussian Noise & Grain (via NumPy)
    img_np = np.array(card).astype(np.float32)
    h, w, c = img_np.shape
    noise = np.random.normal(0, 3.5, (h, w, c)) # Standard deviation of 3.5 adds subtle photographic grain
    noisy_img = np.clip(img_np + noise, 0, 255).astype(np.uint8)
    card = Image.fromarray(noisy_img)
    
    # 10. Apply Environmental Imperfections: Minor Rotation
    card = card.rotate(random.uniform(-0.5, 0.5), resample=Image.BICUBIC, expand=False, fillcolor=(226, 232, 240))
    
    # 11. Apply Environmental Imperfections: Subtle Camera Blur
    card = card.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.5)))
    
    return card

def generate_valid_dates():
    """Generates chronologically and mathematically correct dates using relativedelta."""
    age_today = random.randint(18, 65)
    dob = REF_DATE - relativedelta(years=age_today) - datetime.timedelta(days=random.randint(0, 364))
    
    earliest_issue = dob + relativedelta(years=18)
    nine_years_ago = REF_DATE - relativedelta(years=9)
    actual_earliest = max(earliest_issue, nine_years_ago)
    
    days_between = (REF_DATE - actual_earliest).days
    if days_between <= 0:
        issue_date = REF_DATE - datetime.timedelta(days=random.randint(1, 365))
    else:
        issue_date = actual_earliest + datetime.timedelta(days=random.randint(0, days_between))
        
    expiry_date = issue_date + relativedelta(years=10)
    
    return dob, issue_date, expiry_date

def generate_frankenstein_dates():
    """Generates dates with intentional semantic flaws."""
    flaw_type = random.choice(["expiry_in_past", "issue_before_dob", "underage_at_issue"])
    
    if flaw_type == "expiry_in_past":
        age_today = random.randint(25, 60)
        dob = REF_DATE - relativedelta(years=age_today) - datetime.timedelta(days=random.randint(0, 364))
        issue_date = dob + relativedelta(years=18) + datetime.timedelta(days=random.randint(0, 5 * 365))
        expiry_date = issue_date + relativedelta(years=5)
        if expiry_date >= REF_DATE:
            expiry_date = REF_DATE - datetime.timedelta(days=random.randint(30, 365))
        return dob, issue_date, expiry_date, flaw_type
        
    elif flaw_type == "issue_before_dob":
        age_today = random.randint(20, 50)
        dob = REF_DATE - relativedelta(years=age_today) - datetime.timedelta(days=random.randint(0, 364))
        issue_date = dob - relativedelta(years=random.randint(1, 5))
        expiry_date = REF_DATE + relativedelta(years=random.randint(1, 5))
        return dob, issue_date, expiry_date, flaw_type
        
    else: # "underage_at_issue"
        age_today = random.randint(10, 16)
        dob = REF_DATE - relativedelta(years=age_today) - datetime.timedelta(days=random.randint(0, 364))
        issue_date = dob + relativedelta(years=5)
        expiry_date = REF_DATE + relativedelta(years=random.randint(1, 5))
        return dob, issue_date, expiry_date, flaw_type

def main():
    """Main runner for generating 1,000 hyper-realistic synthetic ID cards."""
    print("Initializing directories...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    metadata = {}
    
    print("Generating 500 Valid IDs...")
    for i in range(1, 501):
        id_num = f"{i:08d}"
        name = fake.name()
        dob, issue, expiry = generate_valid_dates()
        
        img = draw_id_card(id_num, name, dob, issue, expiry)
        filename = f"id_{i:04d}.png"
        img.save(os.path.join(OUTPUT_DIR, filename))
        
        metadata[filename] = {
            "id_number": f"ID-{id_num}",
            "name": name,
            "dob": dob.strftime("%Y-%m-%d"),
            "issue_date": issue.strftime("%Y-%m-%d"),
            "expiry_date": expiry.strftime("%Y-%m-%d"),
            "label": "Valid",
            "flaw_type": "none"
        }
        if i % 100 == 0:
            print(f"Generated {i}/500 Valid IDs")
            
    print("Generating 500 Frankenstein (flawed) IDs...")
    for i in range(501, 1001):
        id_num = f"{i:08d}"
        name = fake.name()
        dob, issue, expiry, flaw_type = generate_frankenstein_dates()
        
        img = draw_id_card(id_num, name, dob, issue, expiry)
        filename = f"id_{i:04d}.png"
        img.save(os.path.join(OUTPUT_DIR, filename))
        
        metadata[filename] = {
            "id_number": f"ID-{id_num}",
            "name": name,
            "dob": dob.strftime("%Y-%m-%d"),
            "issue_date": issue.strftime("%Y-%m-%d"),
            "expiry_date": expiry.strftime("%Y-%m-%d"),
            "label": "Frankenstein",
            "flaw_type": flaw_type
        }
        if (i - 500) % 100 == 0:
            print(f"Generated {i - 500}/500 Frankenstein IDs")
            
    print(f"Saving metadata to {METADATA_PATH}...")
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("Dataset generation complete!")

if __name__ == "__main__":
    main()
