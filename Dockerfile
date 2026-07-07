FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright
RUN pip install playwright
RUN playwright install-deps
RUN playwright install chromium

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for data and logs
RUN mkdir -p data logs

# Expose any necessary ports (if the app has a web interface)
# EXPOSE 8000

# Run the application
# The command will be overridden by docker-compose