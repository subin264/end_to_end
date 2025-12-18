#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""독일 GDPR 데이터를 11개 컬럼 스키마로 변환"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime

SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]

EUR_TO_USD_RATE = 1.08


def safe_str(value):
    """안전하게 문자열 변환"""
    return str(value).strip() if not pd.isna(value) else ""


def parse_date(date_str):
    """DD.MM.YYYY → YYYY-MM-DD"""
    if pd.isna(date_str) or not str(date_str).strip():
        return ""
    try:
        return datetime.strptime(str(date_str).strip(), '%d.%m.%Y').strftime('%Y-%m-%d')
    except:
        return str(date_str).strip()


def extract_fine_amount_usd(fine_str):
    """EUR → USD 변환"""
    if pd.isna(fine_str) or not str(fine_str).strip():
        return "0"
    
    fine_str = str(fine_str).strip()
    eur_match = re.search(r'([\d,\.]+)\s*EUR', fine_str, re.IGNORECASE)
    amount_str = eur_match.group(1) if eur_match else re.findall(r'[\d,\.]+', fine_str)[0] if re.findall(r'[\d,\.]+', fine_str) else None
    
    if amount_str:
        try:
            amount = float(amount_str.replace(',', '').replace('.', ''))
            return str(int(amount * EUR_TO_USD_RATE))
        except:
            pass
    return "0"


def extract_enforcing_agency(decision_by):
    """접두사 제거 (Court:, DPA:)"""
    if pd.isna(decision_by):
        return ""
    
    agency = str(decision_by).strip()
    if agency.startswith(("Court:", "DPA:")):
        agency = agency.split(":", 1)[1].strip()
    return re.sub(r'\s*\([^)]*\)', '', agency).strip()


def get_violation_group(gdpr_articles, decision_type):
    """위반 그룹 분류"""
    text = " ".join([safe_str(gdpr_articles), safe_str(decision_type)]).lower()
    
    if any(k in text for k in ['gdpr', 'article', '15', '6', '9', '82']):
        return 'privacy-related offenses'
    if any(k in text for k in ['competition', 'cartel', 'antitrust']):
        return 'competition-related offenses'
    if any(k in text for k in ['consumer', 'protection', 'uwg']):
        return 'consumer-protection-related offenses'
    return 'other' if text.strip() else ""


def get_violation_type(gdpr_articles, decision_type):
    """위반 유형 추출"""
    articles = safe_str(gdpr_articles)
    if articles:
        mapping = {'15': 'access request violation', '12': 'access request violation',
                   '6': 'lawful basis violation', '9': 'special category data violation',
                   '82': 'damages claim'}
        for key, value in mapping.items():
            if key in articles:
                return value
        return articles[:200]
    
    decision = safe_str(decision_type)
    return decision[:200] if decision else ""


def convert_row_to_schema(row):
    """11개 컬럼 스키마로 변환"""
    return {
        'enforcement_id': safe_str(row.get('Case number/name')),
        'country_code': 'DE',
        'company_name': safe_str(row.get('Parties')),
        'sector': '',
        'violation_group': get_violation_group(row.get('Relevant GDPR articles'), row.get('Type of decision & outcome')),
        'violation_type': get_violation_type(row.get('Relevant GDPR articles'), row.get('Type of decision & outcome')),
        'enforcement_date': parse_date(row.get('Date of decision')),
        'fine_amount_usd': extract_fine_amount_usd(row.get('Fine')),
        'enforcing_agency': extract_enforcing_agency(row.get('Decision by')),
        'summary': safe_str(row.get('Summary')),
        'source_url': ''
    }


def main():
    """메인 처리: 1.csv ~ 18.csv를 읽어서 11개 컬럼 스키마로 변환"""
    input_dir = Path(__file__).parent
    output_file = input_dir / 'violation_tracker_germany_converted.csv'
    all_data = []

    for i in range(1, 19):
        csv_file = input_dir / f'{i}.csv'
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                all_data.extend([convert_row_to_schema(row) for _, row in df.iterrows()])
                print(f"{i}.csv: {len(df)}개 행 처리 완료")
            except Exception as e:
                print(f"{i}.csv 실패: {e}")

    if all_data:
        result_df = pd.DataFrame(all_data)[SCHEMA_COLUMNS]
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n변환 완료: {len(result_df)}개 행 → {output_file}")
    else:
        print("변환할 데이터가 없습니다.")


if __name__ == "__main__":
    main()

