FROM python:3.11-slim

# Install system dependencies for wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    libfontconfig1 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

# Start the app
CMD ["gunicorn", "app:app"]