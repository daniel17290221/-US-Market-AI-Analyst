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
# We use requirements_local.txt as it contains the full set of dependencies for AI and analysis
COPY requirements_local.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure the app runs on port 7860 (Hugging Face Spaces default)
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 7860

# Run the application
# We'll use a slightly modified app.py or just call flask directly
CMD ["python", "app.py"]
