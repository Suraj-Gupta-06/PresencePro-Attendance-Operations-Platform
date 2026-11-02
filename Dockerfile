FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install required system packages for OpenCV, dlib, and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps face-recognition==1.3.0

# Copy application code
COPY . .

# Ensure data directories exist
RUN mkdir -p data/database data/faces data/attendance_captures logs

EXPOSE 5000

# Initialize DB on start and launch Gunicorn
CMD ["sh", "-c", "python init_db.py && gunicorn 'app:create_app()' --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120"]
