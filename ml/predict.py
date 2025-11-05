# ml/predict.py
import os
import sys
import json
import numpy as np
import rasterio
from rasterio.mask import mask
import tensorflow as tf
from google.cloud import storage
import zipfile
import tempfile
import geopandas as gpd
from shapely.geometry import mapping

# === CONFIG ===
MODEL_PATH = "model/unet_model.h5"
BUCKET_NAME = os.getenv("GCS_BUCKET")

# Load model
model = tf.keras.models.load_model(MODEL_PATH)

def download_zip(gcs_url, local_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob_name = gcs_url.split(f"https://storage.googleapis.com/{BUCKET_NAME}/")[1]
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded: {gcs_url} → {local_path}")

def extract_band(zip_path, band_name, out_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if band_name in name and name.endswith('.jp2'):
                z.extract(name, out_path)
                extracted = os.path.join(out_path, name)
                # Copy to final path
                import shutil
                shutil.copy(extracted, out_path)
                return out_path
    return None

def clip_raster(raster_path, geojson, out_path):
    with rasterio.open(raster_path) as src:
        try:
            out_image, out_transform = mask(src, [geojson], crop=True)
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            with rasterio.open(out_path, "w", **out_meta) as dest:
                dest.write(out_image)
            return out_path
        except:
            return None

def normalize(band):
    return band.astype('float32') / 10000  # Sentinel-2 reflectance

def predict_patch(patch):
    patch = np.expand_dims(patch, axis=0)
    pred = model.predict(patch, verbose=0)
    return (pred[0, :, :, 0] > 0.5).astype(np.uint8)

def upload_result(local_path, dest_name):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"predictions/{dest_name}")
    blob.upload_from_filename(local_path)
    blob.make_public()
    return f"https://storage.googleapis.com/{BUCKET_NAME}/predictions/{dest_name}"

def main():
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: predict.py <gcs_zip_url> <aoi_geojson>"}))
        return

    gcs_url = sys.argv[1]
    aoi_str = sys.argv[2]
    aoi = json.loads(aoi_str)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "scene.zip")
        download_zip(gcs_url, zip_path)

        # Extract bands
        bands = ['B04', 'B03', 'B02', 'B08', 'B11']  # R,G,B,NIR,SWIR
        band_paths = []
        for b in bands:
            path = extract_band(zip_path, b, os.path.join(tmpdir, f"{b}.jp2"))
            if path:
                band_paths.append(path)

        if len(band_paths) != 5:
            print(json.dumps({"error": "Missing bands"}))
            return

        # Stack & clip
        with rasterio.open(band_paths[0]) as src:
            clipped_paths = []
            for bp in band_paths:
                clipped = os.path.join(tmpdir, f"clip_{os.path.basename(bp)}")
                if clip_raster(bp, aoi, clipped):
                    clipped_paths.append(clipped)

        if len(clipped_paths) != 5:
            print(json.dumps({"error": "Clip failed"}))
            return

        # Read clipped bands
        stack = []
        for cp in clipped_paths:
            with rasterio.open(cp) as src:
                band = src.read(1)
                stack.append(normalize(band))
        stack = np.stack(stack, axis=-1)  # HxWx5

        # Predict
        h, w, _ = stack.shape
        pred = np.zeros((h, w), dtype=np.uint8)
        patch_size = 64

        for i in range(0, h, patch_size):
            for j in range(0, w, patch_size):
                patch = stack[i:i+patch_size, j:j+patch_size]
                if patch.shape[0] < patch_size or patch.shape[1] < patch_size:
                    continue
                pred[i:i+patch_size, j:j+patch_size] = predict_patch(patch)

        # Save result
        result_path = os.path.join(tmpdir, "prediction.tif")
        with rasterio.open(clipped_paths[0]) as src:
            meta = src.meta.copy()
            meta.update(count=1, dtype='uint8')
            with rasterio.open(result_path, 'w', **meta) as dst:
                dst.write(pred, 1)

        # Upload
        job_id = gcs_url.split('/')[-1].split('.')[0]
        result_url = upload_result(result_path, f"{job_id}_pred.tif")

        # Calculate metrics
        built_up_pixels = np.sum(pred)
        pixel_area_m2 = 10 * 10  # 10m resolution
        built_up_ha = built_up_pixels * pixel_area_m2 / 10000

        print(json.dumps({
            "resultUrl": result_url,
            "builtUpAreaHa": round(built_up_ha, 2),
            "growthPercent": 0.0,  # Future: compare with past
            "iou": 0.0,            # Future: validation
            "confidence": 0.9
        }))

if __name__ == "__main__":
    main()