# Dockerfile — FIXED for Debian 12 (Trixie) — Render Compatible
FROM python:3.11-slim AS python-base

# Install system dependencies for rasterio/GDAL + TensorFlow
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgdal-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libglx-mesa0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    tensorflow==2.16.1 \
    rasterio==1.3.10 \
    geopandas==0.14.1 \
    fiona==1.9.6 \
    shapely==2.0.2 \
    pillow==10.3.0 \
    requests==2.31.0

# Final stage — Node.js
FROM node:20-alpine AS node-base

# Copy Python runtime from python-base
COPY --from=python-base /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=python-base /usr/local/bin /usr/local/bin
COPY --from=python-base /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu

# Set up Node.js app
WORKDIR /app
COPY package*.json ./
RUN npm install --only=production

# Copy source code
COPY . .

# Create folders
RUN mkdir -p uploads/raw-imagery uploads/predictions ml/model

# Expose port
EXPOSE 3000

# Start server
CMD ["node", "src/server.js"]
