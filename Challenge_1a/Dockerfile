FROM --platform=linux/amd64 python:3.10-slim

# Set UTF-8 encoding
ENV LANG=C.UTF-8

# Set working directory
WORKDIR /app

# Install dependencies for pdfminer and font handling (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy script and requirements
COPY process_pdfs.py .
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python", "process_pdfs.py"]
