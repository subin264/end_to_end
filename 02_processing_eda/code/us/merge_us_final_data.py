#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
미국 FTC 데이터 4개 파일을 1개로 합치는 스크립트

목적: us_creating_11_schemas 폴더의 4개 CSV 파일을 합쳐서 최종 파일 생성
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def main():
    """메인 함수: 4개 파일을 합쳐서 최종 파일 생성"""
    # 경로 설정
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent
    input_dir = data_dir / 'us_creating_11_schemas'
    output_dir = data_dir / 'us_the_last_final_1'
    output_dir.mkdir(exist_ok=True)
    
    # 합칠 파일 목록
    input_files = [
        input_dir / 'ftc_merger_enforcement_detailed_20251214_011647_converted_20251214_172941.csv',
        input_dir / 'ftc_nonmerger_enforcement_detailed_20251214_001909_converted_20251214_172941.csv',
        input_dir / 'us_ftc_enforcement_merged_final_converted_20251214_172941.csv',
        input_dir / 'violation_tracker_us_20251214_033305.csv'
    ]
    
    # 각 파일 읽어서 합치기
    all_data = []
    for input_file in input_files:
        if not input_file.exists():
            print(f"파일 없음: {input_file.name}")
            continue
        
        try:
            df = pd.read_csv(input_file, encoding='utf-8-sig')
            all_data.append(df)
            print(f"읽기 완료: {input_file.name} → {len(df)}개 행")
        except Exception as e:
            print(f"오류: {input_file.name} 읽기 실패 - {e}")
    
    if not all_data:
        print("합칠 파일이 없습니다.")
        return
    
    # 모든 데이터 합치기
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 11개 스키마 컬럼 순서로 정렬
    schema_columns = [
        'enforcement_id', 'country_code', 'company_name', 'sector',
        'violation_group', 'violation_type', 'enforcement_date',
        'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
    ]
    merged_df = merged_df[schema_columns]
    
    # 파일명 생성 및 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f'us_final_merged_{timestamp}.csv'
    
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n합치기 완료: 총 {len(merged_df)}개 행")
    print(f"저장 위치: {output_file}")


if __name__ == "__main__":
    main()

