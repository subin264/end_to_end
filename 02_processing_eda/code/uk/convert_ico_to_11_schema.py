"""
ICO 데이터를 11개 스키마로 변환하는 스크립트

입력: ico_all_data_20251205_064229.csv
출력: 11개 컬럼 스키마 CSV 파일
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import re
from typing import Optional

# 상수 정의
SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]

GBP_TO_USD_RATE = 1.27
VIOLATION_GROUP = "privacy-related offenses"
VIOLATION_TYPE = "data_protection"


def parse_date(date_str: str) -> Optional[str]:
    """
    "2 December 2025" → "2025-12-02" 형식으로 변환
    
    Args:
        date_str: 원본 날짜 문자열
        
    Returns:
        ISO 형식 날짜 문자열 (YYYY-MM-DD) 또는 None
    """
    if pd.isna(date_str) or not date_str.strip():
        return None
    
    try:
        # "2 December 2025" 형식 파싱
        dt = datetime.strptime(date_str.strip(), "%d %B %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # 파싱 실패 시 None 반환
        return None


def parse_fine_amount(fine_str: str) -> Optional[float]:
    """
    Fine_Amount 문자열을 USD 금액으로 변환
    
    처리 형식:
    - "£14m" → 14,000,000 × 1.27 = 17,780,000
    - "£1,500 " → 1,500 × 1.27 = 1,905
    - "£200,000 " → 200,000 × 1.27 = 254,000
    - "£290" → 290 × 1.27 = 368.3
    
    Args:
        fine_str: 원본 벌금 문자열
        
    Returns:
        USD 금액 (float) 또는 None
    """
    if pd.isna(fine_str) or not fine_str.strip():
        return None
    
    # £ 제거 및 공백 제거
    cleaned = fine_str.replace("£", "").strip()
    
    if not cleaned:
        return None
    
    # m (million) 처리
    if cleaned.lower().endswith('m'):
        try:
            amount = float(cleaned[:-1].replace(",", ""))
            return amount * 1_000_000 * GBP_TO_USD_RATE
        except ValueError:
            return None
    
    # k (thousand) 처리
    if cleaned.lower().endswith('k'):
        try:
            amount = float(cleaned[:-1].replace(",", ""))
            return amount * 1_000 * GBP_TO_USD_RATE
        except ValueError:
            return None
    
    # 일반 숫자 처리 (콤마 제거)
    try:
        amount = float(cleaned.replace(",", ""))
        return amount * GBP_TO_USD_RATE
    except ValueError:
        return None


def convert_row_to_schema(row: pd.Series, index: int) -> dict:
    """
    원본 행을 11개 스키마로 변환
    
    Args:
        row: 원본 데이터 행
        index: 행 인덱스 (0부터 시작)
        
    Returns:
        11개 컬럼 딕셔너리
    """
    # enforcement_id: "ICO-UK-001" 형식 (001부터 시작, 3자리 zero-padding)
    enforcement_id = f"ICO-UK-{index + 1:03d}"
    
    # country_code: "United Kingdom" → "UK"
    country_code = "UK" if pd.notna(row.get('Country')) else None
    
    # company_name: Company 그대로
    company_name = row.get('Company') if pd.notna(row.get('Company')) else None
    
    # sector: Sector 그대로 (빈 값 허용)
    sector = row.get('Sector') if pd.notna(row.get('Sector')) else None
    
    # violation_group: "privacy-related offenses" 통일
    violation_group = VIOLATION_GROUP
    
    # violation_type: "data_protection" 통일
    violation_type = VIOLATION_TYPE
    
    # enforcement_date: Date 파싱
    enforcement_date = parse_date(row.get('Date'))
    
    # fine_amount_usd: Fine_Amount 파싱 및 USD 변환
    fine_amount_usd = parse_fine_amount(row.get('Fine_Amount'))
    
    # enforcing_agency: Authority 그대로 (ICO)
    enforcing_agency = row.get('Authority') if pd.notna(row.get('Authority')) else None
    
    # summary: 원본에 없으므로 빈 값
    summary = None
    
    # source_url: Source_URL 그대로
    source_url = row.get('Source_URL') if pd.notna(row.get('Source_URL')) else None
    
    return {
        'enforcement_id': enforcement_id,
        'country_code': country_code,
        'company_name': company_name,
        'sector': sector,
        'violation_group': violation_group,
        'violation_type': violation_type,
        'enforcement_date': enforcement_date,
        'fine_amount_usd': fine_amount_usd,
        'enforcing_agency': enforcing_agency,
        'summary': summary,
        'source_url': source_url
    }


def main():
    """메인 처리 함수"""
    # 경로 설정
    script_dir = Path(__file__).parent
    input_file = script_dir.parent / 'ico_all_data_20251205_064229.csv'
    output_dir = script_dir.parent / 'creating_11_schemas'
    output_dir.mkdir(exist_ok=True)
    
    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f'ico_uk_converted_{timestamp}.csv'
    
    # 원본 데이터 읽기 및 변환 처리
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    converted_data = [convert_row_to_schema(row, idx) for idx, row in df.iterrows()]
    
    # DataFrame 생성 및 저장
    result_df = pd.DataFrame(converted_data)[SCHEMA_COLUMNS]
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"변환 완료: {len(result_df)}개 행 → {output_file.name}")


if __name__ == "__main__":
    main()

