# Dockerfile.app
# Base image for Python
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH for module discovery
ENV PYTHONPATH=/app

# Copy application files
COPY . .

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
