#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""독일 데이터 2개 파일 병합"""

import pandas as pd
from pathlib import Path

def main():
    """두 파일을 합쳐서 최종 파일 생성"""
    base_dir = Path(__file__).parent
    final_collector_dir = base_dir.parent / "Final_Collector"
    
    # 파일 경로
    file1 = base_dir / "violation_tracker_germany_converted.csv"
    file2 = final_collector_dir / "violation_tracker_germany_20251214_111255.csv"
    output_file = base_dir / "최종2개 합친파일.csv"
    
    # 파일 읽기
    df1 = pd.read_csv(file1, encoding='utf-8-sig')
    df2 = pd.read_csv(file2, encoding='utf-8-sig')
    
    print(f"파일1: {len(df1)}개 행")
    print(f"파일2: {len(df2)}개 행")
    
    # 병합
    merged_df = pd.concat([df1, df2], ignore_index=True)
    
    # 저장
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n병합 완료: {len(merged_df)}개 행 → {output_file}")


if __name__ == "__main__":
    main()

