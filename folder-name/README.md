# Adobe Hackathon 1A – ML-Based Heading Extractor

## 🧠 Description
This ML pipeline extracts document structure (Title, H1, H2, H3) from PDFs using RandomForest classification.

## 📦 Requirements
- Python 3.9
- Docker (for final submission)

## 🛠 Usage

### Step 1: Generate Training Data
Put sample PDFs and their JSON ground truth into `sample_dataset/pdfs/` and `sample_dataset/outputs/`.

```bash
python generate_training_data.py
```

### Step 2: Train the Model
```bash
python train_model.py
```

### Step 3: Test Locally
```bash
python process_pdfs.py
```

### Step 4: Build Docker Image
```bash
docker build --platform linux/amd64 -t heading-extractor .
```

### Step 5: Run in Docker
```bash
docker run --rm -v $(pwd)/sample_dataset/pdfs:/app/input -v $(pwd)/sample_dataset/outputs:/app/output --network none heading-extractor
```

---

## ✅ Output
Each `pdf` will generate a corresponding `.json` file with:
- `title`
- `outline` list of headings with levels and page numbers

---
