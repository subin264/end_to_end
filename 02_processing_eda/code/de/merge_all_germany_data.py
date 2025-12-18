#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""독일 데이터 모든 변환 파일 병합"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    """모든 변환된 파일을 합쳐서 최종 파일 생성"""
    base_dir = Path(__file__).parent.parent
    converted_dir = base_dir / "3_변환된데이터"
    final_dir = base_dir / "4_최종합친데이터"
    final_dir.mkdir(exist_ok=True)
    
    # 병합할 파일 목록
    files_to_merge = [
        converted_dir / "violation_tracker_germany_converted.csv",  # 1~18.csv 변환
        converted_dir / "enforcement_tracker_germany_converted.csv",  # enforcement_tracker 변환
        converted_dir / "violation_tracker_germany_20251214_111255.csv"  # 스크래핑 데이터
    ]
    
    all_data = []
    
    for file_path in files_to_merge:
        if file_path.exists():
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                all_data.append(df)
                print(f"{file_path.name}: {len(df)}개 행 읽기 완료")
            except Exception as e:
                print(f"{file_path.name} 읽기 실패: {e}")
        else:
            print(f"파일 없음: {file_path.name}")
    
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = final_dir / f'독일_최종합친데이터_{timestamp}.csv'
        
        merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n병합 완료: {len(merged_df)}개 행 → {output_file}")
    else:
        print("병합할 데이터가 없습니다.")


if __name__ == "__main__":
    main()

