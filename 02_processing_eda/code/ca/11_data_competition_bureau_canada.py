#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Competition Bureau Canada 데이터를 11개 컬럼 스키마로 변환
"""

import csv
import re
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M%S'
)
logger = logging.getLogger(__name__)

# 11개 컬럼 스키마 (최종)
SCHEMA_COLUMNS = [
    'enforcement_id', 'country_code', 'company_name', 'sector',
    'violation_group', 'violation_type', 'enforcement_date',
    'fine_amount_usd', 'enforcing_agency', 'summary', 'source_url'
]


def extract_fine_amount(value: str) -> str:
    """벌금액에서 숫자만 추출"""
    if not value or str(value).strip() == '':
        return "0"
    cleaned = re.sub(r'[^\d.]', '', str(value))
    try:
        return str(int(float(cleaned)))
    except:
        return "0"


def parse_date(date_str: str) -> str:
    """날짜 형식 변환 (YYYY-MM-DD)"""
    if not date_str or str(date_str).strip() == '':
        return ""
    date_str = str(date_str).strip()
    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%B %d, %Y', '%Y-%m-%d %H:%M:%S']
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    return date_str


def clean_violation_type(violation_type: str) -> str:
    """violation_type 정제 (너무 긴 경우 요약)"""
    if not violation_type:
        return ""
    
    violation_type = violation_type.strip()
    
    # 너무 긴 경우 (200자 이상) 요약
    if len(violation_type) > 200:
        # 주요 키워드 추출 시도
        keywords = ['drip pricing', 'bid-rigging', 'conspiracy', 'misleading', 
                   'deceptive', 'false advertising', 'anti-competitive', 'cartel']
        for keyword in keywords:
            if keyword.lower() in violation_type.lower():
                return keyword.replace('-', ' ').title()
        # 키워드 없으면 앞부분만
        return violation_type[:100] + "..."
    
    return violation_type


def extract_company_name(row: Dict) -> str:
    """company_name 추출 (긴 설명에서 실제 회사명만 추출)"""
    company_name = row.get('company_name', '').strip()
    sector = row.get('sector', '').strip()
    case_name = row.get('case_name', '').strip()
    
    # company_name이 비어있거나 sector와 같은 경우, 또는 너무 긴 경우
    if not company_name or company_name == sector or len(company_name) > 100:
        # case_name에서 회사명 추출 시도
        if case_name:
            # "Company - Sector" 형식인 경우
            if ' - ' in case_name:
                potential_name = case_name.split(' - ')[0].strip()
                # 너무 길면 패턴으로 추출
                if len(potential_name) > 100:
                    company_name = extract_company_from_text(potential_name)
                else:
                    company_name = potential_name
            else:
                # 긴 설명에서 회사명 추출
                company_name = extract_company_from_text(case_name)
    
    # 여전히 너무 길면 추가 추출
    if len(company_name) > 100:
        company_name = extract_company_from_text(company_name)
    
    return company_name


def extract_company_from_text(text: str) -> str:
    """긴 텍스트에서 회사명 또는 개인명 추출"""
    if not text:
        return ""
    
    # "Criminal charges" 같은 경우는 회사명이 아님
    if text.lower().startswith('criminal charges'):
        return ""
    
    # 패턴 1: 회사명 + 법인 형태 (가장 정확)
    company_patterns = [
        r'^([A-Z][A-Za-z0-9\s&,\.\-]+?(?:Ltd\.|Inc\.|Limited|Company|Corp\.|Ltée))',
        r'([A-Z][A-Za-z0-9\s&,\.\-]+?(?:Ltd\.|Inc\.|Limited|Company|Corp\.|Ltée))',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # "has been ordered" 같은 설명 제거
            if 'has been' in name.lower() or 'will pay' in name.lower():
                name = re.sub(r'\s+(has been|will pay).*', '', name, flags=re.I).strip()
            if 2 <= len(name) <= 80:
                return name
    
    # 패턴 2: "Company Name will pay/pleaded/has been" (회사명만 추출)
    action_patterns = [
        r'^([A-Z][A-Za-z0-9\s&,\.\-]{2,40}?)(?:\s+(?:will pay|pleaded|has been ordered|has been|was ordered))',
        r'^([A-Z][A-Za-z0-9\s&,\.\-]{2,40}?)(?:\s+(?:Ltd\.|Inc\.|Limited|Company|Corp\.|Ltée))',
    ]
    
    for pattern in action_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # 설명 제거
            if ',' in name and len(name) > 30:
                # "Serge Daunais, a former executive" -> "Serge Daunais"
                name = name.split(',')[0].strip()
            if 2 <= len(name) <= 50:
                return name
    
    # 패턴 3: 개인 이름 (이름 + 성)
    person_pattern = r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    match = re.search(person_pattern, text)
    if match:
        name = match.group(1).strip()
        if 3 <= len(name) <= 50:
            return name
    
    # 패턴 4: 일반 회사명 (앞부분만, 최대 40자)
    words = text.split()
    if len(words) > 0:
        # 첫 단어가 대문자로 시작하는 경우
        if words[0][0].isupper():
            potential_name = ' '.join(words[:3])  # 최대 3단어
            if len(potential_name) <= 40:
                return potential_name
    
    # 마지막 시도: 앞부분 40자만
    return text[:40].strip()


def convert_row_to_schema(row: Dict) -> Dict:
    """Competition Bureau 행을 11개 컬럼 스키마로 변환"""
    # 벌금액 추출 (USD)
    fine_amount_usd = extract_fine_amount(row.get('fine_amount_usd', ''))
    
    # 날짜 (enforcement_date 우선, 없으면 violation_date)
    enforcement_date = row.get('enforcement_date', '') or row.get('violation_date', '')
    enforcement_date = parse_date(enforcement_date)
    
    # violation_group (regulation_name에서 추출)
    regulation_name = row.get('regulation_name', '').strip()
    if regulation_name and 'Cartel' in regulation_name:
        violation_group = 'competition-related offenses'
    elif regulation_name:
        violation_group = 'competition-related offenses'
    else:
        violation_group = ''
    
    # company_name 추출 (개선)
    company_name = extract_company_name(row)
    
    # violation_type 정제
    violation_type = clean_violation_type(row.get('violation_type', ''))
    
    # summary 처리 (비어있으면 settlement_type 또는 violation_type 사용, 최대 500자)
    summary = row.get('summary', '').strip()
    if not summary:
        # settlement_type 시도
        settlement_type = row.get('settlement_type', '').strip()
        if settlement_type and len(settlement_type) > 10:  # 의미있는 내용인지 확인
            summary = settlement_type[:500]
        elif violation_type:
            summary = violation_type[:500]
    
    if len(summary) > 500:
        summary = summary[:500]
    
    return {
        'enforcement_id': row.get('enforcement_id', '').strip(),
        'country_code': row.get('country_code', 'CA').strip(),
        'company_name': company_name,
        'sector': row.get('sector', '').strip(),
        'violation_group': violation_group,
        'violation_type': violation_type,
        'enforcement_date': enforcement_date,
        'fine_amount_usd': fine_amount_usd,
        'enforcing_agency': row.get('enforcing_agency', '').strip(),
        'summary': summary,
        'source_url': row.get('source_url', '').strip()
    }


def convert_csv_file(input_file: Path, output_file: Path):
    """CSV 파일 변환"""
    logger.info(f"변환 시작: {input_file.name}")
    
    converted_rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            converted = convert_row_to_schema(row)
            converted_rows.append(converted)
    
    # CSV 저장
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
        writer.writeheader()
        writer.writerows(converted_rows)
    
    logger.info(f"변환 완료: {output_file.name} ({len(converted_rows)}개)")


def main():
    """메인 실행"""
    base_dir = Path(__file__).parent / "canada_data_Sprt"
    
    # 변환할 파일 목록
    input_files = [
        "competition_bureau_canada_raw_20251209_230852.csv",
        "competition_bureau_canada_raw_20251210_015731.csv",
        "competition_bureau_canada_cartel_raw_20251210_020051.csv"
    ]
    
    logger.info("=" * 60)
    logger.info("Competition Bureau 데이터 변환 시작")
    logger.info("=" * 60)
    
    for filename in input_files:
        input_file = base_dir / filename
        if not input_file.exists():
            logger.warning(f"파일 없음: {filename}")
            continue
        
        # 출력 파일명 생성
        output_filename = filename.replace('_raw_', '_converted_').replace('.csv', '_schema.csv')
        output_file = base_dir / output_filename
        
        try:
            convert_csv_file(input_file, output_file)
        except Exception as e:
            logger.error(f"변환 실패 ({filename}): {e}")
    
    logger.info("=" * 60)
    logger.info("변환 완료")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

