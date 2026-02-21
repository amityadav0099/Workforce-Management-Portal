FROM python:3.11-slim

# Install system dependencies for PDF generation
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libfontconfig1 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Start the application
CMD ["gunicorn", "app:app"]

HR_Portal_Secure_Key_2026
omfs pgcg mprh pwau