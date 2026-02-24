FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the app runs on port 7860 (Hugging Face Spaces default)
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]
