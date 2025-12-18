# ====================
# TOPSIS modeling all
# ============================

# ==========================
# Step 1: load and check data
# ====================
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

# =============================
# Step 2: calculate RC scores
# =====================
country_counts = layer2['country_code'].value_counts().reset_index()
country_counts.columns = ['country_code', 'n']
TARGET = 1000
country_counts['weight'] = (TARGET / country_counts['n']).round(3)

country_weights = dict(zip(country_counts['country_code'], country_counts['weight']))
layer2['weight'] = layer2['country_code'].map(country_weights)

# calculate N
N_by_country = layer2.groupby('country_code')['weight'].sum().reset_index()
N_by_country.columns = ['country_code', 'N']

# calculate F
layer2['fine_numeric'] = pd.to_numeric(layer2['fine_amount_usd'], errors='coerce').fillna(0)
F_by_country = (layer2.groupby('country_code').apply(
    lambda x: (x['fine_numeric'] * x['weight']).sum()
).reset_index())
F_by_country.columns = ['country_code', 'F']

# calculate D
def calculate_entropy(group):
    violation_counts = group['violation_group'].value_counts()
    probs = violation_counts / violation_counts.sum()
    return -np.sum(probs * np.log(probs + 1e-10))

D_by_country = layer2.groupby('country_code').apply(calculate_entropy).reset_index()
D_by_country.columns = ['country_code', 'D']

# normalize and calculate RC scores
rc_components = N_by_country.merge(F_by_country, on='country_code').merge(D_by_country, on='country_code')

N_min, N_max = rc_components['N'].min(), rc_components['N'].max()
F_min, F_max = rc_components['F'].min(), rc_components['F'].max()
D_min, D_max = rc_components['D'].min(), rc_components['D'].max()

rc_components['N_norm'] = (rc_components['N'] - N_min) / (N_max - N_min)
rc_components['F_norm'] = (rc_components['F'] - F_min) / (F_max - F_min)
rc_components['D_norm'] = (rc_components['D'] - D_min) / (D_max - D_min)

rc_components['RC_score'] = (
    rc_components['N_norm'] * 0.4 +
    rc_components['F_norm'] * 0.3 +
    rc_components['D_norm'] * 0.3
).round(6)

# ISO code mapping
rc_scores = rc_components[['country_code', 'RC_score']].copy()
rc_scores['ISO'] = rc_scores['country_code'].map(iso_mapping)
rc_scores = rc_scores[['ISO', 'RC_score']].copy()

print("rc scores calculated:")
print(rc_scores.sort_values('RC_score', ascending=False))

# ==========================================================
# Step 3: merge data
# ========================
df = layer3.merge(rc_scores[['ISO', 'RC_score']], on='ISO', how='left')

missing = df.isnull().sum()
if missing.any():
    print(f"missing values: {missing[missing > 0]}")
else:
    print(f"merged data: {len(df)} countries, {len(df.columns)} columns")

print(df[['ISO', 'Country', 'RC_score', 'gdp_per_capita', 'digital_infra_index', 'job_market_index']])

# ====================================
# Step 4: normalize 
# ==========================
def normalize_min_max(series: pd.Series) -> pd.Series:
    """
    min-max normalization (0~1 scale)
    
    basis:
    - check constant series: return 0 if max == min (to avoid division by zero)
    - handle NaN: return NaN if there is NaN in the original data (intended behavior)
    - vectorized operation: apply to the entire pandas Series at once
    """
    s_min = series.min()
    s_max = series.max()
    
    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return pd.Series(0.0, index=series.index)
    
    return (series - s_min) / (s_max - s_min)

# select columns to normalize (TOPSIS input variables)
norm_cols = ['RC_score', 'gdp_per_capita', 'digital_infra_index', 'job_market_index']

# run normalization (vectorized operation)
df_norm = df[norm_cols].apply(normalize_min_max, axis=0)


for col in norm_cols:
    df[f'{col}_norm'] = df_norm[col]

# check for NaN/Inf
if df_norm.isnull().any().any() or np.isinf(df_norm).any().any():
    print("warning: normalized data contains NaN or Inf")
    print(df_norm[df_norm.isnull().any(axis=1)])
else:
    print("normalization completed: all values in 0~1 range")


print("\nnormalized data summary:")
print(df_norm.describe())


print("\nnormalization comparison (sample):")
comparison = df[['ISO'] + norm_cols + [f'{col}_norm' for col in norm_cols]].head(3)
print(comparison)

# =======================
# Step 5: run TOPSIS
# ================================


# implement TOPSIS algorithm
def run_topsis(df_norm, weights, benefit_cols, cost_cols):
    """
    TOPSIS 알고리즘 실행
    
    input:
            - df_norm: Normalized dataframe (contains only normalized columns)
            - weights: List of weights [RC_score, gdp_per_capita, digital_infra_index, job_market_index]
            - benefit_cols: A list of variables that are better the higher the value.
            - cost_cols: A list of variables where lower values ​​are better.
            
        output:
            - scores: TOPSIS score for each country (0~1, higher is better)
            - details: Intermediate calculation results (distance, etc.)
    """
    
    all_cols = benefit_cols + cost_cols
    missing = [c for c in all_cols if c not in df_norm.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    
    if len(set(all_cols)) != len(all_cols):
        raise ValueError("benefit_cols and cost_cols must not overlap")
    
    if len(weights) != len(all_cols):
        raise ValueError(f"weights length ({len(weights)}) != columns length ({len(all_cols)})")
    
    
    weights = np.array(weights)
    w_sum = weights.sum()
    if abs(w_sum - 1.0) > 0.05:
        print(f"warning: weights sum = {w_sum}, normalizing to 1.0")
        weights = weights / w_sum
    
    if (weights < 0).any():
        raise ValueError("weights must be non-negative")
    
    
    weighted = df_norm[all_cols].copy()
    for i, col in enumerate(all_cols):
        weighted[col] = df_norm[col] * weights[i]
    
    # calculate ideal solution
    ideal_positive = pd.Series(index=all_cols, dtype=float)
    ideal_negative = pd.Series(index=all_cols, dtype=float)
    
    for col in benefit_cols:
        ideal_positive[col] = weighted[col].max()
        ideal_negative[col] = weighted[col].min()
    
    for col in cost_cols:
        ideal_positive[col] = weighted[col].min()
        ideal_negative[col] = weighted[col].max()
    
    # Euclidean distance
    dist_positive = np.sqrt(((weighted - ideal_positive) ** 2).sum(axis=1))
    dist_negative = np.sqrt(((weighted - ideal_negative) ** 2).sum(axis=1))
    
    denominator = dist_positive + dist_negative
    denominator = denominator.replace(0, 1e-10)
    
    # calculate TOPSIS score
    scores = dist_negative / denominator
    
    
    details = pd.DataFrame({
        'dist_to_ideal': dist_positive,
        'dist_to_negative_ideal': dist_negative,
        'topsis_score': scores
    })
    
    return scores, details


# map normalized column names
norm_cols_mapping = {
    'RC_score': 'RC_score_norm',
    'gdp_per_capita': 'gdp_per_capita_norm',
    'digital_infra_index': 'digital_infra_index_norm',
    'job_market_index': 'job_market_index_norm'
}


df_norm_for_topsis = df[[f'{col}_norm' for col in norm_cols]].copy()
df_norm_for_topsis.columns = norm_cols

# Benefit/Cost separation
benefit_cols = ['gdp_per_capita', 'digital_infra_index', 'job_market_index']
cost_cols = ['RC_score']

weights_balanced = [0.25, 0.25, 0.25, 0.25]  # [RC_score, gdp, infra, job]


scores, details = run_topsis(df_norm_for_topsis, weights_balanced, benefit_cols, cost_cols)

df['topsis_score'] = scores.values
df['topsis_rank'] = df['topsis_score'].rank(ascending=False).astype(int)


print("\ntopsis results (balanced weights):")
print(df[['ISO', 'Country', 'topsis_score', 'topsis_rank']].sort_values('topsis_score', ascending=False))

print("\ntopsis details:")
print(details)