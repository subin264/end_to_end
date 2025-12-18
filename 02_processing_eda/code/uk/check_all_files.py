#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""폴더 내 모든 파일 확인"""

import pandas as pd
from pathlib import Path

base_dir = Path(__file__).parent

print("=" * 80)
print("파일 목록 및 구조 확인")
print("=" * 80)

# CSV 파일 확인
csv_files = sorted(base_dir.glob("*.csv"))
xlsx_files = sorted(base_dir.glob("*.xlsx"))

for csv_file in csv_files:
    print(f"\n[{csv_file.name}]")
    try:
        # 파일 크기 확인
        file_size = csv_file.stat().st_size / 1024  # KB
        print(f"  크기: {file_size:.1f} KB")
        
        # 첫 몇 줄 읽기
        df = pd.read_csv(csv_file, encoding='utf-8-sig', nrows=5)
        print(f"  컬럼 수: {len(df.columns)}")
        print(f"  컬럼명: {', '.join(df.columns.tolist())}")
        
        # 전체 행 수 확인 (헤더 제외)
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            total_lines = sum(1 for _ in f) - 1
        print(f"  총 행 수: {total_lines:,}행")
        
        # 샘플 데이터 (첫 행)
        if len(df) > 0:
            print(f"  샘플 (첫 행):")
            for col in df.columns[:3]:  # 처음 3개 컬럼만
                val = str(df.iloc[0][col])[:50] if pd.notna(df.iloc[0][col]) else ""
                print(f"    {col}: {val}")
        
    except Exception as e:
        print(f"  오류: {e}")

# XLSX 파일 확인
for xlsx_file in xlsx_files:
    print(f"\n[{xlsx_file.name}]")
    try:
        file_size = xlsx_file.stat().st_size / 1024  # KB
        print(f"  크기: {file_size:.1f} KB")
        
        # 엑셀 파일 읽기
        xl = pd.ExcelFile(xlsx_file)
        print(f"  시트 수: {len(xl.sheet_names)}")
        print(f"  시트명: {', '.join(xl.sheet_names)}")
        
        # 첫 번째 시트 확인
        if xl.sheet_names:
            df = pd.read_excel(xlsx_file, sheet_name=xl.sheet_names[0], nrows=5)
            print(f"  첫 시트 컬럼 수: {len(df.columns)}")
            print(f"  첫 시트 컬럼명: {', '.join(df.columns.tolist()[:5])}...")
            
            # 전체 행 수 확인
            df_full = pd.read_excel(xlsx_file, sheet_name=xl.sheet_names[0])
            print(f"  첫 시트 총 행 수: {len(df_full):,}행")
        
    except Exception as e:
        print(f"  오류: {e}")

print("\n" + "=" * 80)
print("확인 완료")
print("=" * 80)

