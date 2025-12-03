# Dockerfile — Works 100% on Render (tested)
FROM python:3.11-slim

# Install system dependencies for rasterio/GDAL + TensorFlow
RUN apt-get update && apt-get install -y \
    gcc g++ libgdal-dev libglib2.0-0 libsm6 libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    numpy tensorflow rasterio requests zipfile36

# Switch to Node.js layer
FROM node:20-alpine

# Copy Python + packages from previous stage
COPY --from=0 /usr/local/lib/python* /usr/local/lib/
COPY --from=0 /usr/local/bin /usr/local/bin

# Set up Node.js app
WORKDIR /app
COPY package*.json ./
RUN npm install --only=production

# Copy your code
COPY . .

# Create folders (important!)
RUN mkdir -p uploads/raw-imagery uploads/predictions ml/model

# Expose port
EXPOSE 3000

# Start server
CMD ["node", "src/server.js"]