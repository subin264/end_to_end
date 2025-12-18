#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Competition Bureau 변환 데이터를 violation_tracker_canada 파일에 병합
"""

import csv
from pathlib import Path

base_dir = Path(__file__).parent / "canada_data_Sprt"

# 기존 파일
existing_file = base_dir / "violation_tracker_canada_20251214_015121.csv"

# 변환된 파일들
converted_files = [
    base_dir / "competition_bureau_canada_converted_20251209_230852_schema.csv",
    base_dir / "competition_bureau_canada_converted_20251210_015731_schema.csv",
    base_dir / "competition_bureau_canada_cartel_converted_20251210_020051_schema.csv"
]

# 스키마 (13개 컬럼)
schema = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'fine_amount_original', 'currency',
    'enforcing_agency', 'summary', 'source_url'
]

# 기존 파일 읽기
print(f"기존 파일 읽기: {existing_file.name}")
existing_data = []
with open(existing_file, 'r', encoding='utf-8-sig') as f:
    existing_data = list(csv.DictReader(f))
print(f"기존 데이터: {len(existing_data)}개")

# 변환된 파일들 읽기 및 변환
new_data = []
for converted_file in converted_files:
    if not converted_file.exists():
        print(f"파일 없음: {converted_file.name}")
        continue
    
    print(f"변환 파일 읽기: {converted_file.name}")
    file_count = 0
    with open(converted_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 11개 컬럼 → 13개 컬럼 변환
            new_row = {
                'enforcement_id': row.get('enforcement_id', ''),
                'country_code': row.get('country_code', ''),
                'company_name': row.get('company_name', ''),
                'sector': row.get('sector', ''),
                'violation_group': row.get('violation_group', ''),
                'violation_type': row.get('violation_type', ''),
                'enforcement_date': row.get('enforcement_date', ''),
                'fine_amount_usd': row.get('fine_amount_usd', ''),
                'fine_amount_original': '',
                'currency': '',
                'enforcing_agency': row.get('enforcing_agency', ''),
                'summary': row.get('summary', ''),
                'source_url': row.get('source_url', '')
            }
            new_data.append(new_row)
            file_count += 1
    print(f"  추가: {file_count}개")

merged_data = existing_data + new_data
print(f"병합 완료: 총 {len(merged_data)}개 (기존 {len(existing_data)}개 + 신규 {len(new_data)}개)")

print(f"저장 중: {existing_file.name}")
with open(existing_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=schema)
    writer.writeheader()
    writer.writerows(merged_data)

print("완료")
