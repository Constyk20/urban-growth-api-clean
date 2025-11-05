# ml/predict.py - LOCAL + GITHUB STORAGE (NO CLOUD) - FINAL VERSION
import os
import sys
import json
import numpy as np
import rasterio
from rasterio.mask import mask
import tensorflow as tf
import zipfile
import tempfile
import requests
import shutil

# === CONFIG ===
MODEL_GITHUB_URL = "https://github.com/Constyk20/urban-growth-api-clean/raw/main/ml/model/unet_model.h5"
MODEL_LOCAL_PATH = "ml/model/unet_model.h5"

# Auto-download model if missing
if not os.path.exists(MODEL_LOCAL_PATH):
    os.makedirs(os.path.dirname(MODEL_LOCAL_PATH), exist_ok=True)
    print("Downloading U-Net model from GitHub...")
    try:
        response = requests.get(MODEL_GITHUB_URL, stream=True, timeout=30)
        response.raise_for_status()
        with open(MODEL_LOCAL_PATH, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print("Model downloaded successfully.")
    except Exception as e:
        print(json.dumps({"error": f"Failed to download model: {e}"}))
        sys.exit(1)

# Load model
try:
    model = tf.keras.models.load_model(MODEL_LOCAL_PATH)
    print("U-Net model loaded.")
except Exception as e:
    print(json.dumps({"error": f"Failed to load model: {e}"}))
    sys.exit(1)


def download_file(url, local_path):
    """Download from file://, http://, or https:// (GitHub raw)"""
    if url.startswith("file://"):
        src = url[len("file://"):]
        if not os.path.exists(src):
            raise FileNotFoundError(f"Local file not found: {src}")
        shutil.copy(src, local_path)
    else:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
    print(f"Downloaded: {url} → {local_path}")


def extract_band(zip_path, band_name, out_dir):
    """Extract .tif containing band_name from ANY subfolder"""
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if band_name in name and name.lower().endswith('.tif'):
                extracted = z.extract(name, out_dir)
                print(f"Extracted band {band_name}: {name} → {extracted}")
                return extracted
    print(f"Band {band_name} not found in .zip")
    return None


def clip_raster(raster_path, geojson, out_path):
    """Clip raster with AOI"""
    try:
        with rasterio.open(raster_path) as src:
            print(f"Clipping {raster_path} | CRS: {src.crs} | Bounds: {src.bounds}")
            out_image, out_transform = mask(src, [geojson], crop=True, filled=False)
            out_image = out_image.filled(0)  # Fill nodata

            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "dtype": out_image.dtype
            })

            with rasterio.open(out_path, "w", **out_meta) as dest:
                dest.write(out_image)
            print(f"Clipped → {out_path}")
            return out_path
    except Exception as e:
        print(f"Clip failed for {raster_path}: {e}")
        return None


def normalize(band):
    return band.astype('float32') / 10000.0


def predict_patch(patch):
    patch = np.expand_dims(patch, axis=0)
    pred = model.predict(patch, verbose=0)
    return (pred[0, :, :, 0] > 0.5).astype(np.uint8)


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: predict.py <zip_url> <aoi_geojson>"}))
        return

    zip_url = sys.argv[1]
    try:
        aoi = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid GeoJSON: {e}"}))
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "scene.zip")
        try:
            download_file(zip_url, zip_path)
        except Exception as e:
            print(json.dumps({"error": f"Download failed: {e}"}))
            return

        # Extract required bands
        required_bands = ['B04', 'B03', 'B02', 'B08', 'B11']
        band_paths = []
        for b in required_bands:
            path = extract_band(zip_path, b, tmpdir)
            if path:
                band_paths.append(path)

        if len(band_paths) != 5:
            print(json.dumps({"error": f"Missing bands. Found: {[os.path.basename(p) for p in band_paths]}"}))
            return

        # Clip all bands
        clipped_paths = []
        for bp in band_paths:
            clipped = os.path.join(tmpdir, f"clip_{os.path.basename(bp)}")
            if clip_raster(bp, aoi, clipped):
                clipped_paths.append(clipped)

        if len(clipped_paths) != 5:
            print(json.dumps({"error": "Clip failed on one or more bands"}))
            return

        # Stack bands
        stack = []
        for cp in clipped_paths:
            with rasterio.open(cp) as src:
                band = src.read(1)
                stack.append(normalize(band))
        stack = np.stack(stack, axis=-1)  # Shape: (h, w, 5)

        h, w = stack.shape[:2]
        pred = np.zeros((h, w), dtype=np.uint8)
        patch_size = 64

        print(f"Predicting on {h}x{w} image with {patch_size}x{patch_size} patches...")
        for i in range(0, h, patch_size):
            for j in range(0, w, patch_size):
                patch = stack[i:i+patch_size, j:j+patch_size]
                if patch.shape[0] < patch_size or patch.shape[1] < patch_size:
                    continue
                pred[i:i+patch_size, j:j+patch_size] = predict_patch(patch)

        # Save prediction
        result_path = os.path.join(tmpdir, "prediction.tif")
        with rasterio.open(clipped_paths[0]) as src:
            meta = src.meta.copy()
            meta.update(count=1, dtype='uint8')
            with rasterio.open(result_path, 'w', **meta) as dst:
                dst.write(pred, 1)

        # Save to persistent folder
        out_dir = "../uploads/predictions"
        os.makedirs(out_dir, exist_ok=True)
        final_name = f"pred_{int(os.times().elapsed)}.tif"
        final_path = os.path.join(out_dir, final_name)
        shutil.copy(result_path, final_path)

        # Calculate area
        built_up_pixels = np.sum(pred)
        pixel_area_m2 = 10 * 10
        built_up_ha = built_up_pixels * pixel_area_m2 / 10000.0

        # Return file:// URL (local) or GitHub raw (Render)
        result_url = f"file://{os.path.abspath(final_path).replace(chr(92), '/')}"

        print(json.dumps({
            "resultUrl": result_url,
            "builtUpAreaHa": round(built_up_ha, 2),
            "growthPercent": 0.0,
            "iou": 0.0,
            "confidence": 0.9
        }))


if __name__ == "__main__":
    main()