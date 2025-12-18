# ===============================
# Step 1: load and check data
# =======================
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent  # 03_Modeling/

base_dir = project_dir / "Final_use_data"
cache_dir = script_dir / ".cache"
cache_dir.mkdir(exist_ok=True)

layer1_path = base_dir / "layer1_regulation_metadata.csv"
layer2_path = base_dir / "layer2_final_data.csv"
layer3_path = base_dir / "2_mag_layer3_market_talent_2024_fixed.csv"

layer1_cache = cache_dir / "layer1.pkl"
layer2_cache = cache_dir / "layer2.pkl"
layer3_cache = cache_dir / "layer3.pkl"

# if the cached file exists and is newer than the original, use the cache, otherwise load the CSV and save to cache
if layer1_cache.exists() and layer1_cache.stat().st_mtime > layer1_path.stat().st_mtime:
    layer1 = pd.read_pickle(layer1_cache)
    print("layer1 loaded from cache")
else:
    layer1 = pd.read_csv(layer1_path)
    layer1.to_pickle(layer1_cache)
    print(f"layer1: {len(layer1)} rows, {len(layer1.columns)} columns")

if layer2_cache.exists() and layer2_cache.stat().st_mtime > layer2_path.stat().st_mtime:
    layer2 = pd.read_pickle(layer2_cache)
    print("layer2 loaded from cache")
else:
    layer2 = pd.read_csv(layer2_path)
    layer2.to_pickle(layer2_cache)
    print(f"layer2: {len(layer2)} rows, {len(layer2.columns)} columns")

if layer3_cache.exists() and layer3_cache.stat().st_mtime > layer3_path.stat().st_mtime:
    layer3 = pd.read_pickle(layer3_cache)
    print("layer3 loaded from cache")
else:
    layer3 = pd.read_csv(layer3_path)
    layer3.to_pickle(layer3_cache)
    print(f"layer3: {len(layer3)} rows, {len(layer3.columns)} columns")

iso_mapping = {"US": "USA", "UK": "GBR", "DE": "DEU", "CA": "CAN", "AU": "AUS", "KR": "KOR"}
layer2_iso = set(layer2['country_code'].map(iso_mapping).unique())
layer3_iso = set(layer3['ISO'].unique())
common = layer2_iso & layer3_iso
print(f"common countries: {len(common)}/6")
