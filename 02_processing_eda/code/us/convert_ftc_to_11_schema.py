#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FTC 파일을 11개 스키마로 변환하는 스크립트

목적: 3개 FTC CSV 파일을 읽어서 11개 컬럼 스키마로 변환 후 저장
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime


# 11개 스키마 컬럼 순서
SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]

# violation_group 분류를 위한 키워드
PRIVACY_KEYWORDS = ['privacy', 'security', 'coppa', 'data_breach']
COMPETITION_KEYWORDS = [
    'monopoly', 'restraint of trade', 'price fixing', 'collusion', 
    'conspiracy', 'market allocation', 'exclusive dealing'
]


def clean_text(value):
    """빈 값이나 None을 빈 문자열로 변환"""
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()


def format_date(date_str):
    """날짜를 YYYY-MM-DD 형식으로 변환"""
    if not date_str or pd.isna(date_str):
        return ""
    
    date_str = str(date_str).strip()
    
    # 이미 올바른 형식이면 그대로 반환
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # YYYY.M.D 형식을 YYYY-MM-DD로 변환
    if '.' in date_str:
        try:
            year, month, day = date_str.split('.')
            month = month.zfill(2)
            day = day.zfill(2) if day else '01'
            return f"{year}-{month}-{day}"
        except:
            return ""
    
    return date_str


def format_amount(amount_str):
    """금액을 정수 문자열로 변환"""
    if not amount_str or pd.isna(amount_str):
        return "0"
    
    try:
        amount = float(str(amount_str).strip())
        return str(int(amount))
    except:
        return "0"


def classify_violation_group(violation_type):
    """violation_type을 분석해서 violation_group 결정"""
    if not violation_type or pd.isna(violation_type):
        return 'consumer protection-related offenses'
    
    violation_lower = str(violation_type).lower()
    
    # Privacy 키워드가 있으면 privacy-related
    for keyword in PRIVACY_KEYWORDS:
        if keyword in violation_lower:
            return 'privacy-related offenses'
    
    # Competition 키워드가 있으면 competition-related
    for keyword in COMPETITION_KEYWORDS:
        if keyword in violation_lower:
            return 'competition-related offenses'
    
    # 나머지는 consumer protection
    return 'consumer protection-related offenses'


def convert_one_row(row):
    """한 행의 데이터를 11개 스키마로 변환"""
    return {
        'enforcement_id': clean_text(row.get('enforcement_id', '')),
        'country_code': clean_text(row.get('country_code', '')),
        'company_name': clean_text(row.get('company_name', '')),
        'sector': clean_text(row.get('sector', '')),
        'violation_group': classify_violation_group(row.get('violation_type', '')),
        'violation_type': clean_text(row.get('violation_type', '')),
        'enforcement_date': format_date(row.get('enforcement_date', '')),
        'fine_amount_usd': format_amount(row.get('fine_amount_usd', '')),
        'enforcing_agency': clean_text(row.get('enforcing_agency', '')),
        'summary': clean_text(row.get('summary', '')),
        'source_url': clean_text(row.get('source_url', ''))
    }


def convert_csv_file(input_file, output_dir):
    """CSV 파일 하나를 변환해서 저장"""
    # 파일 읽기
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except Exception as e:
        print(f"오류: {input_file.name} 파일을 읽을 수 없습니다 - {e}")
        return None
    
    # 각 행 변환
    converted_rows = []
    for idx, row in df.iterrows():
        converted_row = convert_one_row(row)
        converted_rows.append(converted_row)
    
    # DataFrame 만들기
    result_df = pd.DataFrame(converted_rows)
    result_df = result_df[SCHEMA_COLUMNS]
    
    # 파일명 만들기
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_file.stem}_converted_{timestamp}.csv"
    output_file = output_dir / output_filename
    
    # 저장
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"완료: {input_file.name} → {len(result_df)}개 행")
    
    return output_file


def main():
    """메인 함수: 3개 파일을 변환"""
    # 경로 설정
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent
    output_dir = data_dir / 'us_creating_11_schemas'
    output_dir.mkdir(exist_ok=True)
    
    # 변환할 파일 목록
    input_files = [
        data_dir / 'ftc_merger_enforcement_detailed_20251214_011647.csv',
        data_dir / 'ftc_nonmerger_enforcement_detailed_20251214_001909.csv',
        data_dir / 'us_ftc_enforcement_merged_final.csv'
    ]
    
    # 각 파일 변환
    converted_count = 0
    for input_file in input_files:
        if not input_file.exists():
            print(f"파일 없음: {input_file.name}")
            continue
        
        result = convert_csv_file(input_file, output_dir)
        if result:
            converted_count += 1
    
    # 결과 출력
    print(f"\n총 {converted_count}개 파일 변환 완료")
    print(f"저장 위치: {output_dir}")


if __name__ == "__main__":
    main()
