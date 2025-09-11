# Stage 1: Builder for dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install pip packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.11-slim

WORKDIR /app

# Install curl + dnsutils + wget for DNS + network tools
RUN apt-get update && \
    apt-get install -y wget curl dnsutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Download pre-trained model files
RUN mkdir -p model/v1 && \
    wget "yourblobstorageurltofilehere" -O model/v1/BreastCancerCNN_custom_model.keras && \
    wget "yourblobstorageurltofilehere" -O model/v1/BreastCancerCNN_EfficientNet_model.keras

# Copy application source code
COPY . .

# Expose FastAPI port
EXPOSE 8002

# Launch FastAPI using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]