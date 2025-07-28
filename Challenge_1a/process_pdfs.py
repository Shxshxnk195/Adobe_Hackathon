import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar

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

from pdfminer.layout import LTChar, LTTextLine

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
                avg_size = props["avg_size"]
                styles = props["styles"]
                y_position = props["y_position"]

                if page_num == 1:
                    font_sizes_seen.setdefault(avg_size, []).append(text)

                if is_heading(text, avg_size, styles, y_position, prev_y):
                    level = classify_heading_level(avg_size)
                    headings.append({
                        "level": level,
                        "text": text,
                        "page": page_num
                    })

                prev_y = y_position

    if font_sizes_seen:
        largest_font = max(font_sizes_seen.keys())
        title = font_sizes_seen[largest_font][0]

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
if __name__ == "__main__":
    pdf_file = r"Challenge_1a/sample_dataset/pdfs/file05.pdf"  # Replace with your actual file
    output_file = "output.json"

    result = extract_headings_from_pdf(pdf_file)
    save_outline_to_json(result, output_file)
