"""영국 데이터 4개 파일을 1개로 합치는 스크립트"""

import pandas as pd
from pathlib import Path
from datetime import datetime

SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]


def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / 'creating_11_schemas'
    output_dir = script_dir.parent / 'the_last_final_1'
    output_dir.mkdir(exist_ok=True)
    
    # CSV 파일 자동 찾기
    csv_files = list(input_dir.glob('*.csv'))
    if not csv_files:
        print("합칠 파일이 없습니다.")
        return
    
    # 모든 CSV 파일 읽어서 합치기
    dfs = [pd.read_csv(f, encoding='utf-8-sig') for f in csv_files]
    merged_df = pd.concat(dfs, ignore_index=True)[SCHEMA_COLUMNS]
    
    # 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f'uk_final_merged_{timestamp}.csv'
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"합치기 완료: {len(merged_df)}개 행 → {output_file.name}")


if __name__ == "__main__":
    main()

