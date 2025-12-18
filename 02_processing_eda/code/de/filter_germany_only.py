#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
저장된 CSV 파일에서 독일, 영국 데이터 필터링하여 새 파일로 저장
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def filter_countries(input_file: str, output_dir: str = None):
    """CSV 파일에서 독일, 영국 데이터 필터링"""
    input_path = Path(input_file)
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 독일 데이터 필터링
    df_germany = df[df['Country'].str.contains('GERMANY', case=False, na=False)]
    output_file_de = output_dir / f"enforcement_tracker_germany_filtered_{timestamp}.csv"
    df_germany.to_csv(output_file_de, index=False, encoding='utf-8-sig')
    print(f"독일: {len(df)}개 → {len(df_germany)}개 (저장: {output_file_de})")
    
if __name__ == "__main__":
    input_file = "/Users/baesubin/Desktop/데이터 수집_end_to_end/2_Part 2_Data_Collection_Total_File/3_DE_data_coll/Final_Collector/enforcement_tracker_germany_20251213_172807.csv"
    filter_countries(input_file)
