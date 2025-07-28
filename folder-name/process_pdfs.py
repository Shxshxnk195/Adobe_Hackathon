import os
import fitz
import joblib
import json

INPUT_DIR = "sample_dataset/pdfs"
OUTPUT_DIR = "sample_dataset/outputs"


model = joblib.load("heading_classifier.pkl")
le = joblib.load("label_encoder.pkl")

def extract_features_for_inference(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        lines = page.get_text("dict")["blocks"]
        for block in lines:
            for line in block.get("lines", []):
                text = " ".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue

                span = line["spans"][0]
                font = span["font"]
                blocks.append({
                    "text": text,
                    "features": [
                        span["size"],
                        int("Bold" in font),
                        int(text.isupper()),
                        line["bbox"][1],
                        len(text),
                        page_num
                    ],
                    "page": page_num
                })

    return blocks

def predict_headings(blocks):
    predictions = []
    for block in blocks:
        pred = model.predict([block["features"]])[0]
        label = le.inverse_transform([pred])[0]
        if label != "Other":
            predictions.append({
                "level": label,
                "text": block["text"],
                "page": block["page"]
            })
    return predictions

for file in os.listdir(INPUT_DIR):
    if not file.endswith(".pdf"):
        continue

    path = os.path.join(INPUT_DIR, file)
    blocks = extract_features_for_inference(path)
    preds = predict_headings(blocks)

    title = next((p["text"] for p in preds if p["level"] == "Title"), "Untitled Document")
    outline = [p for p in preds if p["level"] != "Title"]

    output = {
        "title": title,
        "outline": outline
    }

    output_path = os.path.join(OUTPUT_DIR, file.replace(".pdf", ".json"))
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Processed {file} -> {output_path}")
