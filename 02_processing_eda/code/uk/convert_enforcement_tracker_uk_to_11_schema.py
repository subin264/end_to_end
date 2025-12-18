"""
enforcement_tracker_uk_filtered 파일을 11개 컬럼 스키마로 변환

독일 변환 스크립트와 동일한 구조, 영국 데이터에 맞게 수정
"""

import pandas as pd
import re
from pathlib import Path

SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]

EUR_TO_USD_RATE = 1.08


def safe_str(value):
    """안전하게 문자열 변환"""
    return str(value).strip() if not pd.isna(value) else ""


def extract_enforcement_id(etid_str):
    """ETid에서 enforcement_id 추출"""
    if pd.isna(etid_str):
        return ""
    etid_str = str(etid_str).strip()
    match = re.search(r'ETid-\d+', etid_str)
    return match.group(0) if match else etid_str.split('|')[0].strip()


def get_country_code(country_str):
    """국가명 → 국가 코드 변환 (UNITED KINGDOM → UK)"""
    if pd.isna(country_str):
        return ""
    country = str(country_str).upper()
    if 'UNITED KINGDOM' in country or 'UK' in country:
        return 'UK'
    return country[:2] if len(country) >= 2 else ""


def extract_fine_amount_usd(fine_str):
    """EUR → USD 변환"""
    if pd.isna(fine_str) or not str(fine_str).strip():
        return None
    
    fine_str = str(fine_str).strip().replace('"', '').replace(',', '')
    
    # 숫자 추출
    numbers = re.findall(r'\d+', fine_str)
    if numbers:
        try:
            amount = int(''.join(numbers))
            return float(amount * EUR_TO_USD_RATE)
        except:
            pass
    return None


def extract_all_urls(source, column_13, etid):
    """모든 URL 추출 후 세미콜론으로 연결"""
    urls = []
    text = " ".join([safe_str(source), safe_str(column_13), safe_str(etid)])
    
    # URL 패턴 추출
    url_pattern = r'https?://[^\s\|\)]+'
    found_urls = re.findall(url_pattern, text)
    
    # 중복 제거 후 정렬
    unique_urls = sorted(set(found_urls))
    return '; '.join(unique_urls) if unique_urls else ""


def convert_row_to_schema(row):
    """11개 컬럼 스키마로 변환"""
    return {
        'enforcement_id': extract_enforcement_id(row.get('ETid')),
        'country_code': get_country_code(row.get('Country')),
        'company_name': safe_str(row.get('Controller/Processor')),
        'sector': safe_str(row.get('Column_8')),
        'violation_group': safe_str(row.get('Quoted Art.')),
        'violation_type': safe_str(row.get('Type')),
        'enforcement_date': safe_str(row.get('Date of Decision')),
        'fine_amount_usd': extract_fine_amount_usd(row.get('Fine [€]')),
        'enforcing_agency': safe_str(row.get('Column_4')),
        'summary': safe_str(row.get('Column_11')),
        'source_url': extract_all_urls(row.get('Source'), row.get('Column_13'), row.get('ETid'))
    }


def main():
    """메인 처리"""
    script_dir = Path(__file__).parent
    input_file = script_dir.parent / 'enforcement_tracker_uk_filtered_20251213_180425.csv'
    output_dir = script_dir.parent / 'creating_11_schemas'
    output_dir.mkdir(exist_ok=True)
    
    if not input_file.exists():
        print(f"파일을 찾을 수 없습니다: {input_file}")
        return
    
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    all_data = [convert_row_to_schema(row) for _, row in df.iterrows()]
    
    result_df = pd.DataFrame(all_data)[SCHEMA_COLUMNS]
    output_file = output_dir / 'enforcement_tracker_uk_converted.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"변환 완료: {len(result_df)}개 행 → {output_file.name}")


if __name__ == "__main__":
    main()

