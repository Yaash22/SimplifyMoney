# Use Python 3.8 slim image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Create a script to run both services
COPY start.sh .
RUN chmod +x start.sh

 