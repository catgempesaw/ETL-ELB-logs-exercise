FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY elb_log_to_mysql.py .
COPY .env .

# Entrypoint
CMD ["python", "elb_log_to_mysql.py"]