FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt pyproject.toml ./
COPY craft/ ./craft/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[all]"

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV CRAFT_LOG_LEVEL=INFO

# Expose port for API (when implemented)
EXPOSE 8000

# Default command
CMD ["python", "-c", "import craft; print(f'CRAFT v{craft.__version__} ready!')"]
