import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from pdfminer.layout import LTChar, LTTextLine
import re
import os
import json
from pathlib import Path


def is_noise_line(text):
    """Filter out lines that are unlikely to be actual headings."""
    import re

    text = text.strip()
    text_lower = text.lower()

    # Ignore empty or whitespace-only lines
    if not text:
        return True
        # Allow some common heading patterns even if they look short
    if re.match(r"^(section|chapter|appendix|article)\s+\w+", text_lower):
        return False

    # Ignore long numeric strings (IDs, phone numbers, etc.)
    if re.fullmatch(r"[\d\s\-()+]{5,}", text):
        return True
    # Ignore lines that end with a period
    if text.endswith('.'):
        return True

    # Ignore standalone long numbers (5+ digits)
    if re.fullmatch(r"\d{5,}", text):
        return True

    # Ignore alphanumeric IDs like "ID123456" or "Ref: 87654321"
    if re.fullmatch(r"[a-zA-Z]{1,5}[\s:\-]?\d{4,}", text):
        return True

    # Ignore version numbers like "1.0.2"
    if re.fullmatch(r"\d+(\.\d+)+", text):
        return True

    # Ignore URLs
    if re.search(r"\b(?:https?:\/\/)?(?:www\.)?\S+\.(com|org|net|gov|edu|in)\b", text_lower):
        return True

    # Ignore emails
    if re.search(r"\b\S+@\S+\.\S+\b", text_lower):
        return True

    # Ignore dates
    if re.search(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b", text_lower):
        return True

    # Ignore address-like lines with number + ALL CAPS (like "3735 PARKWAY")
    if re.fullmatch(r"\d+\s+[A-Z\s]{3,}", text):
        return True

    # Ignore lines ending in 3+ non-alphanumeric characters (e.g., "RSVP: -----")
    if re.search(r"[:\-_.•●]{3,}\s*$", text):
        return True

    # Ignore lines with mostly symbols or decorations
    if re.fullmatch(r"[^\w\s]{3,}", text) or re.fullmatch(r"[-=_.•●]{3,}", text):
        return True

    # Ignore common label lines
    if text_lower in {
        "form type", "page", "signature", "date", "document", "form", "attachment", "name", "email", "rsvp"
    }:
        return True

    # Ignore short lowercase lines
    if len(text.split()) <= 2 and text == text.lower():
        return True

    return False



def is_heading(text, avg_size, styles, y_position, prev_y):
    """Determine if a text line is a heading based on heuristics."""
    if len(text.split()) > 15:
        return False

    is_bold = any("Bold" in style or "bold" in style for style in styles)
    is_upper = text.isupper()

    score = 0
    if avg_size >= 14:
        score += 2
    if is_bold:
        score += 2
    if is_upper:
        score += 1
    if abs(prev_y - y_position) > 20:
        score += 1

    return score >= 3

def classify_heading_level(avg_size):
    """Classify the heading into H1, H2, H3 based on font size."""
    if avg_size >= 16:
        return "H1"
    elif avg_size >= 13:
        return "H2"
    else:
        return "H3"



def extract_text_properties(text_line):
    if not hasattr(text_line, "__iter__") or not isinstance(text_line, LTTextLine):
        return None  # Prevents error if called on LTChar or similar

    text = text_line.get_text().strip()
    chars = [char for char in text_line if isinstance(char, LTChar)]
    if not text or not chars:
        return None

    sizes = [char.size for char in chars]
    fonts = [char.fontname for char in chars]
    avg_size = round(sum(sizes) / len(sizes), 2)
    styles = set(fonts)
    y_position = text_line.y1

    return {
        "text": text,
        "avg_size": avg_size,
        "styles": styles,
        "y_position": y_position,
    }


def extract_headings_from_pdf(pdf_path):
    """Main logic to extract the headings and title from the PDF."""
    headings = []
    font_sizes_seen = {}
    heading_font_sizes = set()
    prev_y = 1000
    title = ""

    for page_num, layout in enumerate(extract_pages(pdf_path), start=1):
        for element in layout:
            if not isinstance(element, LTTextContainer):
                continue

            for text_line in element:
                props = extract_text_properties(text_line)
                if not props:
                    continue

                text = props["text"]
                if is_noise_line(text):
                    continue

                avg_size = props["avg_size"]
                styles = props["styles"]
                y_position = props["y_position"]

                if y_position < 100:
                    continue

                if page_num == 1:
                    font_sizes_seen.setdefault(avg_size, []).append(text)

                if is_heading(text, avg_size, styles, y_position, prev_y):
                    heading_font_sizes.add(avg_size)
                    headings.append({
                        "font_size": avg_size,
                        "text": text.strip(),
                        "page": page_num
                    })

                prev_y = y_position

    # Dynamically classify heading levels based on font size rankings
    sorted_sizes = sorted(heading_font_sizes, reverse=True)
    font_to_level = {}

    if not sorted_sizes:
        print(f"⚠️  No headings detected in {pdf_path}.")
        return {
            "title": "",
            "outline": []
        }

    if len(sorted_sizes) == 1:
        font_to_level[sorted_sizes[0]] = "H1"
    elif len(sorted_sizes) == 2:
        font_to_level[sorted_sizes[0]] = "H1"
        font_to_level[sorted_sizes[1]] = "H2"
    else:
        font_to_level[sorted_sizes[0]] = "H1"
        font_to_level[sorted_sizes[1]] = "H2"
        font_to_level[sorted_sizes[2]] = "H3"

    # Assign heading levels
    for h in headings:
        h["level"] = font_to_level.get(h["font_size"], "H3")
        del h["font_size"]

    # Extract title as largest font on page 1
    if font_sizes_seen:
        largest_font = max(font_sizes_seen.keys())
        title_candidates = font_sizes_seen[largest_font]
        title = title_candidates[0].strip() if title_candidates else ""

    return {
        "title": title,
        "outline": headings
    }

def save_outline_to_json(data, output_path):
    """Save the extracted data to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Done. Output written to {output_path}")

# ---------- Entry Point ----------
def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        result = extract_headings_from_pdf(str(pdf_file))
        output_file = output_dir / f"{pdf_file.stem}.json"
        
        save_outline_to_json(result, output_file)
        
        print(f"Saved to: {output_file.name}")

if __name__ == "__main__":
    print("Starting processing pdfs")
    process_pdfs()
    print("Completed processing pdfs")
