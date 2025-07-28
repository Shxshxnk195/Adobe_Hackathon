import os
import fitz  # PyMuPDF
import json
import pandas as pd

INPUT_DIR = "sample_dataset/pdfs"
OUTPUT_DIR = "sample_dataset/outputs"

def load_ground_truth(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    gt_map = {}
    for item in data["outline"]:
        gt_map[(item["text"].strip(), item["page"])] = item["level"]
    return gt_map, data["title"]

def extract_features(pdf_path, gt_map, title_text):
    doc = fitz.open(pdf_path)
    rows = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                text = " ".join([span["text"] for span in line["spans"]]).strip()
                if not text or len(text) < 2:
                    continue

                size = line["spans"][0]["size"]
                font = line["spans"][0]["font"]
                y_pos = line["bbox"][1]

                is_bold = "Bold" in font
                is_caps = text.isupper()

                label = "Other"
                key = (text.strip(), page_idx + 1)
                if key in gt_map:
                    label = gt_map[key]
                elif text == title_text:
                    label = "Title"

                rows.append({
                    "text": text,
                    "font_size": size,
                    "is_bold": int(is_bold),
                    "is_caps": int(is_caps),
                    "y_pos": y_pos,
                    "page": page_idx + 1,
                    "text_length": len(text),
                    "label": label
                })

    return rows

all_rows = []
for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".pdf"):
        continue

    pdf_path = os.path.join(INPUT_DIR, filename)
    json_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
    gt_map, title = load_ground_truth(json_path)
    rows = extract_features(pdf_path, gt_map, title)
    all_rows.extend(rows)

df = pd.DataFrame(all_rows)
df.to_csv("training_data.csv", index=False)
print(f"✅ Training data saved to training_data.csv ({len(df)} rows)")
