

# ==============================
# TOPSIS result validation script (sensitivity + consistency check)
# ==============================

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys

warnings.filterwarnings("ignore")


# -------------------------
# 0. reuse common resources from topsis_modeling.py
# ---------------------------------------------------------
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import topsis_modeling  # noqa: E402

df = topsis_modeling.df.copy()
df_norm_for_topsis = topsis_modeling.df_norm_for_topsis.copy()
benefit_cols = topsis_modeling.benefit_cols
cost_cols = topsis_modeling.cost_cols
run_topsis = topsis_modeling.run_topsis

# keep scenario weights local to avoid cross-module coupling
# weights: [RC_score, gdp_per_capita, digital_infra_index, job_market_index]
scenarios = {
    "balanced": [0.25, 0.25, 0.25, 0.25],
    "talent_focused": [0.20, 0.20, 0.20, 0.40],
    "regulation_focused": [0.40, 0.20, 0.20, 0.20],
    "market_focused": [0.20, 0.40, 0.20, 0.20],
    "infra_focused": [0.20, 0.20, 0.40, 0.20],
}


# ----------------------------
# 1. create a table of ranks by scenario
# -------------------------------------
def get_ranks_by_scenario() -> pd.DataFrame:
    """각 시나리오별 TOPSIS 순위를 한 테이블로 정리."""
    records = []
    for scenario_name, weights in scenarios.items():
        scores, _ = run_topsis(
            df_norm_for_topsis, weights, benefit_cols, cost_cols
        )
        # df의 순서(행 인덱스)를 기준으로 ISO, Country와 매칭
        rank = scores.rank(ascending=False, method="min").astype(int)
        for idx, r in rank.items():
            iso = df.iloc[idx]["ISO"]
            country = df.iloc[idx]["Country"]
            records.append(
                {
                    "scenario": scenario_name,
                    "ISO": iso,
                    "Country": country,
                    "rank": int(r),
                }
            )
    return pd.DataFrame(records)


# ----------------------------
# 2. validate consistency between scenarios (based on balanced)
# -------------------------------------
def check_consistency(ranks: pd.DataFrame) -> pd.DataFrame:
    """balanced 순위를 기준으로 시나리오별 순위 변화 요약."""
    base = (
        ranks[ranks["scenario"] == "balanced"]
        .set_index("ISO")["rank"]
        .sort_index()
    )

    rows = []
    for scenario_name in scenarios.keys():
        cur = (
            ranks[ranks["scenario"] == scenario_name]
            .set_index("ISO")["rank"]
            .sort_index()
        )
        diff = (cur - base).abs()
        # 스피어만 상관은 rank 간 상관으로 근사
        rho = np.corrcoef(base.values, cur.values)[0, 1]
        rows.append(
            {
                "scenario": scenario_name,
                "spearman_like_corr": round(float(rho), 3),
                "max_rank_diff": int(diff.max()),
                "mean_rank_diff": round(float(diff.mean()), 2),
            }
        )
    return pd.DataFrame(rows)


# ------------------------------
# 3. sensitivity analysis: perturb weights by ±10%
# -------------------------------------
def perturb_weights(base_weights: list[float], idx: int, delta: float) -> list[float]:
    """지정된 인덱스 가중치를 ±delta 비율로 조정 후 다시 정규화."""
    w = np.array(base_weights, dtype=float)
    w[idx] = w[idx] * (1.0 + delta)
    w = np.clip(w, 0.0, None)
    s = w.sum()
    if s == 0:
        return base_weights
    return list((w / s).round(4))


def sensitivity_around_scenario(
    scenario_name: str, deltas: list[float] | None = None
) -> pd.DataFrame:
    """특정 시나리오 주변 가중치 민감도 분석."""
    if deltas is None:
        deltas = [-0.1, 0.1]  # ±10%

    base_weights = scenarios[scenario_name]
    base_scores, _ = run_topsis(
        df_norm_for_topsis, base_weights, benefit_cols, cost_cols
    )
    base_rank = base_scores.rank(ascending=False, method="min").astype(int)

    rows = []
    feature_names = ["RC_score", "gdp_per_capita", "digital_infra_index", "job_market_index"]

    for i, name in enumerate(feature_names):
        for delta in deltas:
            new_w = perturb_weights(base_weights, i, delta)
            scores, _ = run_topsis(
                df_norm_for_topsis, new_w, benefit_cols, cost_cols
            )
            rank = scores.rank(ascending=False, method="min").astype(int)
            diff = (rank - base_rank).abs()
            rho = np.corrcoef(base_rank.values, rank.values)[0, 1]
            rows.append(
                {
                    "scenario": scenario_name,
                    "feature": name,
                    "delta": delta,
                    "weights": new_w,
                    "spearman_like_corr": round(float(rho), 3),
                    "max_rank_diff": int(diff.max()),
                    "mean_rank_diff": round(float(diff.mean()), 2),
                }
            )
    return pd.DataFrame(rows)


# ----------------------------
# 4. compare single metric ranks with TOPSIS ranks (logical check)
# -----------------------------------------
def compare_with_single_metric(metric: str, scenario_name: str = "balanced") -> pd.DataFrame:
    """단일 지표 순위와 TOPSIS 순위를 비교해 논리성 확인."""
    weights = scenarios[scenario_name]
    scores, _ = run_topsis(
        df_norm_for_topsis, weights, benefit_cols, cost_cols
    )
    topsis_rank = scores.rank(ascending=False, method="min").astype(int)

    if metric == "RC_score":
        series = df["RC_score"]
        single_rank = series.rank(ascending=True, method="min").astype(int)
    else:
        series = df[metric]
        single_rank = series.rank(ascending=False, method="min").astype(int)

    # 인덱스를 기준으로 순위를 맞추고, df의 행 순서와 매칭
    single_rank = single_rank.reindex(topsis_rank.index)
    diff = (topsis_rank - single_rank).abs()
    rho = np.corrcoef(topsis_rank.values, single_rank.values)[0, 1]

    rows = []
    for idx, topsis_r in topsis_rank.items():
        iso = df.iloc[idx]["ISO"]
        country = df.iloc[idx]["Country"]
        rows.append(
            {
                "ISO": iso,
                "Country": country,
                "topsis_rank": int(topsis_r),
                "single_rank": int(single_rank.iloc[idx]),
                "abs_diff": int(diff.iloc[idx]),
            }
        )

    summary = pd.DataFrame(rows).sort_values("topsis_rank", ascending=True)
    summary.attrs["spearman_like_corr"] = round(float(rho), 3)
    return summary


# --------------------------------
# 5-main execution

# ------------------------------------------------------------
if __name__ == "__main__":
    print("loading ranks by scenario...")
    ranks = get_ranks_by_scenario()

    print("\nconsistency check (balanced vs other scenarios):")
    consistency_df = check_consistency(ranks)
    print(consistency_df.to_string(index=False))

    print("\nsensitivity around talent_focused (±10% per feature):")
    sens_talent = sensitivity_around_scenario("talent_focused")
    print(sens_talent.to_string(index=False))

    print("\ncompare balanced topsis vs single metric: gdp_per_capita")
    cmp_gdp = compare_with_single_metric("gdp_per_capita", scenario_name="balanced")
    print(cmp_gdp.to_string(index=False))
    print(f"spearman-like corr (balanced vs gdp): {cmp_gdp.attrs['spearman_like_corr']}")

    print("\ncompare balanced topsis vs single metric: job_market_index")
    cmp_job = compare_with_single_metric("job_market_index", scenario_name="balanced")
    print(cmp_job.to_string(index=False))
    print(f"spearman-like corr (balanced vs job_market_index): {cmp_job.attrs['spearman_like_corr']}")


