# ml/create_mock_zip.py - REAL EPSG:4326 (degrees)
import zipfile
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

# REAL-WORLD: Nairobi area, 64x64 pixels at 10m resolution
size = 64
pixel_size_m = 10

# Top-left corner in DEGREES (lon, lat)
lon_west = 36.8
lat_north = -1.2

# Approximate meters per degree at equator
meters_per_deg = 111320
transform = from_origin(lon_west, lat_north, pixel_size_m / meters_per_deg, pixel_size_m / meters_per_deg)

bands = {
    'B04': np.random.randint(500, 2500, (size, size), dtype=np.uint16),
    'B03': np.random.randint(600, 2600, (size, size), dtype=np.uint16),
    'B02': np.random.randint(700, 2700, (size, size), dtype=np.uint16),
    'B08': np.random.randint(1000, 4000, (size, size), dtype=np.uint16),
    'B11': np.random.randint(300, 2000, (size, size), dtype=np.uint16),
}

os.makedirs("../uploads/raw-imagery", exist_ok=True)
zip_path = "../uploads/raw-imagery/test_mock.zip"

with zipfile.ZipFile(zip_path, 'w') as z:
    for name, data in bands.items():
        tif_path = f"FAKE_S2_B{name}.tif"
        with rasterio.open(
            tif_path, 'w',
            driver='GTiff',
            height=size, width=size,
            count=1, dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data, 1)
        z.write(tif_path, f"GRANULE/L1C_T32NCH_A036789_20210701T101021/IMG_DATA/R10m/{tif_path}")
        os.remove(tif_path)

print(f"EPSG:4326 mock .zip created: {os.path.abspath(zip_path)}")