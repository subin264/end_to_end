import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

input_dir = Path("/Users/baesubin/Desktop/데이터 수집_end_to_end/2_EDA/3_Final_usage_GDP_Talent_Infra")
output_dir = Path("/Users/baesubin/Desktop/데이터 수집_end_to_end/2_EDA/3_Final_usage_GDP_Talent_Infra")
output_dir.mkdir(exist_ok=True, parents=True)

# 셀 2: GDP/인프라 데이터 로드
gdp_path = input_dir / "GDP_AI_Preparedness_Index_Target_Countries_20251215_031628.csv"
gdp = pd.read_csv(gdp_path)

gdp = gdp.rename(columns={
    "GDP per capita (current US$)": "gdp_per_capita",
    "Digitial Infrastructure": "digital_infra_index",
    "Secure Internet servers (per 1 million people)": "secure_servers_per_million"
})

gdp = gdp[["ISO", "Country", "gdp_per_capita", "digital_infra_index", "secure_servers_per_million"]].copy()

# 셀 3: 인재 데이터 로드
talent_path = input_dir / "talent_job_market_index.csv"
talent = pd.read_csv(talent_path)

talent = talent[["ISO", "job_market_index"]].copy()

# 셀 4: 병합
layer3 = gdp.merge(talent, on="ISO", how="left")
layer3 = layer3[["ISO", "Country", "gdp_per_capita", "digital_infra_index", "job_market_index", "secure_servers_per_million"]].copy()

# 셀 5: 저장
layer3_output_path = output_dir / "layer3_market_talent_2024_fixed.csv"
layer3.to_csv(layer3_output_path, index=False, encoding="utf-8-sig")
print(f"layer3 data saved to: {layer3_output_path}")
print(layer3)