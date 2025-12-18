#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
minimal processing script (colab-friendly).

keeps:
- base path: /content/drive/MyDrive/2_EDA
- input folder: 2_Final_Usage_Cases_Country (6 country csvs)
- outputs (utf-8-sig):
  - layer2_final_data.csv
  - rc_scores.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# colab mount (safe in colab; harmless if already mounted)
from google.colab import drive  # type: ignore

drive.mount("/content/drive")


# paths (keep as-is)
BASE_DIR = Path("/content/drive/MyDrive/2_EDA")
DATA_DIR = BASE_DIR / "2_Final_Usage_Cases_Country"
OUTPUT_DIR = BASE_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


COUNTRY_FILES: Dict[str, str] = {
    "US": "1_us_cases.csv",
    "UK": "2_uk_cases.csv",
    "DE": "3_de_cases.csv",
    "AU": "4_australia_cases.csv",
    "CA": "5_canada_cases.csv",
    "KR": "6_South_korea_cases.csv",
}

ENCODINGS_TO_TRY: List[str] = ["utf-8", "utf-8-sig", "latin-1"]

ISO_MAPPING: Dict[str, str] = {"US": "USA", "UK": "GBR", "DE": "DEU", "CA": "CAN", "AU": "AUS", "KR": "KOR"}


VIOLATION_KEYWORDS: Dict[str, List[str]] = {
    "financial": [
        "investor",
        "bank",
        "securit",
        "insurance",
        "mortgage",
        "tax",
        "money laundering",
        "anti-money laundering",
    ],
    "privacy": [
        "data_protection",
        "data protection",
        "privacy",
        "lawful basis",
        "access request",
        "legal basis",
        "technical measures",
        "special category data",
        "gdpr",
        "gdpr compliance",
        "non-compliance with gdpr",
    ],
    "competition": ["anti-competitive", "anticompetitive", "monopoly", "restraint of trade"],
    "consumer": ["consumer", "deceptive", "unfair", "off-label", "controlled substances", "healthcare", "drug"],
    "labor": ["labor", "labour", "employment", "workplace", "wage", "workplace safety"],
    "environmental": ["environmental", "air pollution", "water pollution", "waste", "emission"],
}


def load_layer2_inputs(data_dir: Path) -> pd.DataFrame:
    dfs = []
    for country_code, filename in COUNTRY_FILES.items():
        fp = data_dir / filename
        if not fp.exists():
            raise FileNotFoundError(f"missing input file: {fp}")

        last_err = None
        for enc in ENCODINGS_TO_TRY:
            try:
                df = pd.read_csv(fp, encoding=enc)
                df["country_code"] = country_code
                df["source_file"] = fp.name
                dfs.append(df)
                last_err = None
                break
            except UnicodeDecodeError:
                last_err = f"unicode decode error ({enc})"
        if last_err is not None:
            raise ValueError(f"failed to read {fp.name}: {last_err}")

    return pd.concat(dfs, ignore_index=True)


def classify_violation_group(text: object) -> str:
    if pd.isna(text):
        return "other"
    t = str(text).lower()
    for group, kws in VIOLATION_KEYWORDS.items():
        if any(k in t for k in kws):
            return group
    return "other"


def build_layer2(df: pd.DataFrame, drop_environmental: bool = True) -> pd.DataFrame:
    out = df.copy()

    # normalize GB -> UK (keep convention)
    if "country_code" in out.columns:
        out["country_code"] = out["country_code"].astype(str).str.upper().replace({"GB": "UK"})

    out["violation_type_raw"] = out.get("violation_type")
    out["violation_group"] = out["violation_type_raw"].apply(classify_violation_group)

    # optional remap inside "other"
    if "violation_type" in out.columns:
        t = out["violation_type"].fillna("").astype(str).str.lower()
        healthcare_mask = t.str.contains(
            r"off-label|controlled substances|healthcare provider|medical equipment|drug|healthcare",
            na=False,
            regex=True,
        )
        out.loc[healthcare_mask & (out["violation_group"] == "other"), "violation_group"] = "consumer"

        tax_mask = t.str.contains(r"tax|taxation", na=False, regex=True)
        out.loc[tax_mask & (out["violation_group"] == "other"), "violation_group"] = "financial"

    if drop_environmental:
        out = out[out["violation_group"] != "environmental"].copy()

    return out


def min_max(s: pd.Series) -> pd.Series:
    s_min, s_max = float(s.min()), float(s.max())
    if s_max == s_min:
        return pd.Series(0.0, index=s.index)
    return (s - s_min) / (s_max - s_min)


def calculate_entropy(vg: pd.Series) -> float:
    counts = vg.value_counts()
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log(probs + 1e-10)))


def compute_rc_scores(layer2: pd.DataFrame, target: int = 1000) -> Tuple[pd.DataFrame, pd.DataFrame]:
    country_counts = layer2["country_code"].value_counts().reset_index()
    country_counts.columns = ["country_code", "n"]
    country_counts["weight"] = (target / country_counts["n"]).round(3)

    weight_map = dict(zip(country_counts["country_code"], country_counts["weight"]))
    tmp = layer2.copy()
    tmp["weight"] = tmp["country_code"].map(weight_map).fillna(1.0)
    tmp["fine_numeric"] = pd.to_numeric(tmp.get("fine_amount_usd", 0), errors="coerce").fillna(0)

    n_by = tmp.groupby("country_code")["weight"].sum().reset_index(name="N")
    f_by = (
        tmp.groupby("country_code")
        .apply(lambda x: float((x["fine_numeric"] * x["weight"]).sum()))
        .reset_index(name="F")
    )
    d_by = tmp.groupby("country_code").apply(lambda x: calculate_entropy(x["violation_group"])).reset_index(name="D")

    rc = n_by.merge(f_by, on="country_code").merge(d_by, on="country_code")
    rc["N_norm"] = min_max(rc["N"])
    rc["F_norm"] = min_max(rc["F"])
    rc["D_norm"] = min_max(rc["D"])
    rc["RC_score"] = (0.4 * rc["N_norm"] + 0.3 * rc["F_norm"] + 0.3 * rc["D_norm"]).round(6)

    rc_out = rc[["country_code", "RC_score"]].copy()
    rc_out["ISO"] = rc_out["country_code"].map(ISO_MAPPING)
    rc_out = rc_out[["ISO", "RC_score"]].sort_values("ISO")

    # validation helper
    country_counts["effective_n"] = (country_counts["n"] * country_counts["weight"]).round(1)
    return rc_out, country_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="build layer2 + rc scores (colab path fixed)")
    parser.add_argument("--keep-environmental", action="store_true", help="do not drop 'environmental' rows")
    parser.add_argument("--skip-rc", action="store_true", help="only build layer2_final_data.csv")
    parser.add_argument("--target", type=int, default=1000, help="target effective n for country weights (default: 1000)")
    args = parser.parse_args()

    print("base_dir:", BASE_DIR)
    print("data_dir:", DATA_DIR)
    print("output_dir:", OUTPUT_DIR)

    raw = load_layer2_inputs(DATA_DIR)
    layer2 = build_layer2(raw, drop_environmental=not args.keep_environmental)

    layer2_path = OUTPUT_DIR / "layer2_final_data.csv"
    layer2.to_csv(layer2_path, index=False, encoding="utf-8-sig")
    print("saved:", layer2_path, "| rows:", len(layer2))

    if args.skip_rc:
        return

    rc_scores, country_counts = compute_rc_scores(layer2, target=args.target)
    rc_path = OUTPUT_DIR / "rc_scores.csv"
    rc_scores.to_csv(rc_path, index=False, encoding="utf-8-sig")
    print("saved:", rc_path)

    max_gap = float((country_counts["effective_n"] - args.target).abs().max())
    print("country weight validation max gap:", max_gap)


if __name__ == "__main__":
    main()


