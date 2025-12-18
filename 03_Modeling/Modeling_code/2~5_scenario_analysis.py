# scenario analysis: rerun topsis with different business weights and compare rankings
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys
warnings.filterwarnings("ignore")

# reuse the pre-computed normalized inputs and run_topsis() from topsis_modeling.py
# note: importing topsis_modeling executes that script once (by design in this project)
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

import topsis_modeling

# topsis_modeling.py에서 이미 계산된 변수들 재사용
df_norm_for_topsis = topsis_modeling.df_norm_for_topsis
benefit_cols = topsis_modeling.benefit_cols
cost_cols = topsis_modeling.cost_cols
df = topsis_modeling.df
run_topsis = topsis_modeling.run_topsis

print("reusing pre-computed data from topsis_modeling.py")
print(f"normalized data shape: {df_norm_for_topsis.shape}")
print(f"benefit cols: {benefit_cols}")
print(f"cost cols: {cost_cols}")
print(f"countries: {len(df)}")

# Defining weights by scenario
# weights: [RC_score, gdp_per_capita, digital_infra_index, job_market_index]
scenarios = {
    "balanced": [0.25, 0.25, 0.25, 0.25],  # Equal weighting (default)
    "talent_focused": [0.20, 0.20, 0.20, 0.40],  # Talent-focused (AI startups)
    "regulation_focused": [0.40, 0.20, 0.20, 0.20],  # Regulatory focus (finance, healthcare)
    "market_focused": [0.20, 0.40, 0.20, 0.20],  # Market focus (B2C expansion)
    "infra_focused": [0.20, 0.20, 0.40, 0.20],  # Infrastructure-focused (cloud-based)
}

# 가중치 검증
for name, w in scenarios.items():
    if abs(sum(w) - 1.0) > 0.01:
        print(f"warning: scenario '{name}' weights sum = {sum(w)}")

# 각 시나리오별 TOPSIS 실행 및 결과 저장
scenario_results = []

for scenario_name, weights in scenarios.items():
    scores, details = run_topsis(df_norm_for_topsis, weights, benefit_cols, cost_cols)
    
    result_df = df[['ISO', 'Country']].copy()
    result_df['topsis_score'] = scores.values
    result_df['topsis_rank'] = result_df['topsis_score'].rank(ascending=False).astype(int)
    result_df['scenario'] = scenario_name
    
    scenario_results.append(result_df)

# 모든 시나리오 결과 통합
all_scenarios = pd.concat(scenario_results, ignore_index=True)

# 시나리오별 순위 출력
print("\n" + "="*80)
print("scenario analysis: ranking comparison")
print("="*80)

for scenario_name in scenarios.keys():
    scenario_df = all_scenarios[all_scenarios['scenario'] == scenario_name].copy()
    scenario_df = scenario_df.sort_values('topsis_score', ascending=False)
    
    print(f"\n{scenario_name.upper()} scenario:")
    print(f"weights: {scenarios[scenario_name]}")
    print(f"[RC_score, GDP, Infra, Job]")
    print(scenario_df[['ISO', 'Country', 'topsis_score', 'topsis_rank']].to_string(index=False))

# 시나리오별 1위 국가 비교
print("\n" + "="*80)
print("scenario comparison: top country by scenario")
print("="*80)

top_by_scenario = []
for scenario_name in scenarios.keys():
    scenario_df = all_scenarios[all_scenarios['scenario'] == scenario_name].copy()
    top_country = scenario_df.loc[scenario_df['topsis_rank'].idxmin()]
    top_by_scenario.append({
        'scenario': scenario_name,
        'top_country': top_country['Country'],
        'top_iso': top_country['ISO'],
        'top_score': top_country['topsis_score']
    })

top_summary = pd.DataFrame(top_by_scenario)
print(top_summary.to_string(index=False))

# 국가별 시나리오별 순위 요약
print("\n" + "="*80)
print("country ranking summary across scenarios")
print("="*80)

rank_summary = []
for iso in df['ISO'].unique():
    country_name = df[df['ISO'] == iso]['Country'].iloc[0]
    country_scenarios = all_scenarios[all_scenarios['ISO'] == iso].copy()
    
    avg_rank = country_scenarios['topsis_rank'].mean()
    min_rank = country_scenarios['topsis_rank'].min()
    max_rank = country_scenarios['topsis_rank'].max()
    
    rank_summary.append({
        'ISO': iso,
        'Country': country_name,
        'avg_rank': round(avg_rank, 2),
        'min_rank': int(min_rank),
        'max_rank': int(max_rank),
        'rank_range': f"{int(min_rank)}-{int(max_rank)}"
    })

rank_summary_df = pd.DataFrame(rank_summary).sort_values('avg_rank')
print(rank_summary_df.to_string(index=False))

# 결과 저장 (선택적)
output_dir = Path(__file__).resolve().parent
all_scenarios.to_csv(output_dir / "scenario_analysis_results.csv", index=False, encoding="utf-8-sig")
print(f"\nscenario analysis results saved to: {output_dir / 'scenario_analysis_results.csv'}")

