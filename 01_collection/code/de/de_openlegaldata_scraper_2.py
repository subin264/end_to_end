"""
독일 OpenLegalData API를 통한 법원 판결 데이터 수집
https://de.openlegaldata.io/
"""
import requests
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import time
import os

async def scrape_basic_data():
    output_dir = Path(os.getenv("OPENLEGALDATA_OUTPUT_DIR", str(Path.cwd())))
    output_dir.mkdir(exist_ok=True, parents=True)
    
    api_key = os.getenv("OPENLEGALDATA_API_KEY")
    if not api_key:
        raise RuntimeError("OPENLEGALDATA_API_KEY 환경변수가 필요합니다.")
    
    headers = {
        'Authorization': f'Token {api_key}',
        'Accept': 'application/json'
    }
    
    base_url = "https://de.openlegaldata.io/api/cases/"
    
    print("Collecting list.......")
    
    response = requests.get(base_url, params={'page': 1, 'page_size': 1}, headers=headers)
    data = response.json()
    total_cases = data.get('count', 0)
    print(f"Total cases: {total_cases:,}")
    
    company_keywords = {
        "GmbH": 3, "AG": 3, "Ltd": 2, "Limited": 2,
        "Unternehmen": 1, "Firma": 1, "Gesellschaft": 1, 
        "Konzern": 1, "Betrieb": 1, "Gewerbe": 1
    }
    
    all_company_cases = []
    page = 1
    page_size = 100
    max_cases = 5000
    
    print(f"Company related cases collection started (maximum {max_cases} cases by relevance)...")
    
    while True:
        print(f"Page {page} processing... (currently {len(all_company_cases)} company-related cases found)")
        
        try:
            response = requests.get(base_url, params={'page': page, 'page_size': page_size}, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            cases = data.get('results', [])
            if not cases:
                print("No more cases")
                break
            
            for case_data in cases:
                content = case_data.get('content', '').lower()
                content_original = case_data.get('content', '')
                
                # 관련도 점수 계산
                relevance_score = 0
                matched_keywords = []
                
                for keyword, weight in company_keywords.items():
                    count = content.count(keyword.lower())
                    if count > 0:
                        relevance_score += count * weight
                        matched_keywords.append(keyword)
                
                # 기업 관련 케이스인지 확인 (점수가 0보다 크면)
                if relevance_score > 0:
                    court = case_data.get('court', {})
                    
                    # Court Jurisdiction를 Sector로 사용
                    sector = court.get('jurisdiction', '') if court else ''
                    
                    # 기업명 추출
                    company_name = ""
                    if content_original:
                        # HTML 태그 제거
                        text = re.sub(r'<[^>]+>', ' ', content_original)
                        text = re.sub(r'\s+', ' ', text)
                        
                        # 기업명 패턴 찾기
                        patterns = [
                            r'\b([A-ZÄÖÜ][a-zA-ZäöüÄÖÜß\s&\.\-]{3,}(?:GmbH|AG|Ltd|Limited|SE|KG|OHG|GbR|UG|mbH))\b',
                            r'gegen\s+([A-ZÄÖÜ][a-zA-ZäöüÄÖÜß\s&\.\-]{3,}(?:GmbH|AG|Ltd|Limited|SE|KG|OHG|GbR|UG|mbH))\b',
                        ]
                        
                        companies = []
                        for pattern in patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            for match in matches:
                                cleaned = match.strip()
                                excluded_terms = ['Tenor', 'Urteil', 'Beschluss', 'Kläger', 'Beklagte', 'Antrag']
                                if (len(cleaned) > 5 and len(cleaned) < 100 and 
                                    not any(term in cleaned for term in excluded_terms)):
                                    companies.append(cleaned)
                        
                        if companies:
                            company_name = max(companies, key=len)
                            # 기업명이 추출되면 추가 점수
                            relevance_score += 5
                    
                    # Content 길이에 따른 보너스 (너무 짧으면 감점)
                    content_length = len(content_original) if content_original else 0
                    if content_length > 1000:
                        relevance_score += 2
                    elif content_length < 200:
                        relevance_score -= 1
                    
                    # ICO 스타일 컬럼 구조로 저장 (점수 포함)
                    all_company_cases.append({
                        'Company': company_name if company_name else '',
                        'Fine_Amount': '',
                        'Date': case_data.get('date', ''),
                        'Sector': sector,
                        'Type': case_data.get('type', ''),
                        'Country': 'Germany',
                        'Authority': 'OpenLegalData',
                        'Source_URL': f"https://de.openlegaldata.io/cases/{case_data.get('slug', '')}" if case_data.get('slug') else '',
                        'PDF_URL': '',
                        '_relevance_score': relevance_score  # 정렬용 점수 (나중에 제거)
                    })
            
            print(f"Page {page}: {len(cases)} cases scanned, {len(all_company_cases)} company-related cases found")
            
            # 다음 페이지 확인
            if not data.get('next'):
                print("No more pages")
                break
            
            page += 1
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    print(f"\nTotal {len(all_company_cases)} company-related cases found")
    print("Sorting by relevance score...")
    
    # 관련도 점수로 정렬 (내림차순)
    all_company_cases.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
    
    # 상위 max_cases개만 선택
    results = all_company_cases[:max_cases]
    
    # 정렬용 점수 컬럼 제거
    for case in results:
        case.pop('_relevance_score', None)
    
    print(f"Top {len(results)} cases selected by relevance")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(results)
    
    # ICO 스타일 컬럼 순서로 정렬
    columns_order = [
        'Company', 'Fine_Amount', 'Date', 'Sector', 'Type',
        'Country', 'Authority', 'Source_URL', 'PDF_URL'
    ]
    
    # 존재하는 컬럼만 선택
    existing_columns = [col for col in columns_order if col in df.columns]
    df = df[existing_columns]
    
    csv_file = output_dir / f"5_de_openlegaldata_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    print(f"\nCompleted: {csv_file}")
    print(f"  - total {len(df)}")
    print(f"  - columns: {', '.join(df.columns.tolist())}")
    
    return df

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_basic_data())

