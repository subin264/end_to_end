#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Violation Tracker Global Scraper
Collection of data on violations of Korean jurisdiction
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from urllib.parse import quote_plus

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_DOMAIN = "https://violationtrackerglobal.goodjobsfirst.org"
TARGET_COUNT = 335


@dataclass
class ViolationTrackerConfig:
    """config"""
    base_url: str = BASE_DOMAIN
    timeout: int = 8
    max_retries: int = 2
    delay_between_requests: float = 0.1
    jurisdiction: str = "South Korea"
    
    @property
    def schema_columns(self) -> List[str]:
        """13-column schema"""
        return [
            'enforcement_id', 'country_code', 'company_name', 'sector',
            'violation_group', 'violation_type', 'enforcement_date',
            'fine_amount_usd', 'fine_amount_original', 'currency',
            'enforcing_agency', 'summary', 'source_url'
        ]


def create_session() -> requests.Session:
    """create http session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    return session


def fetch_page(session: requests.Session, url: str, config: ViolationTrackerConfig) -> Optional[BeautifulSoup]:
    """fetch page (with retry)"""
    for attempt in range(config.max_retries):
        try:
            resp = session.get(url, timeout=config.timeout)
            if resp.status_code == 403:
                time.sleep(0.2)
                continue
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            if attempt == config.max_retries - 1:
                logger.error(f"page load failed: {url} - {e}")
                return None
            time.sleep(0.05)
    return None


def build_search_url(config: ViolationTrackerConfig) -> str:
    """build search url"""
    return (
        f"{config.base_url}/summary?"
        f"company_op=starts&company=&"
        f"reporting_date_parent_op=starts&reporting_date_parent=&"
        f"penalty_op=%3E&penalty=&"
        f"offense_group=&"
        f"jurisdiction%5B%5D={quote_plus(config.jurisdiction)}&"
        f"free_text="
    )


def build_page_url(base_url: str, page: int) -> str:
    """build page url"""
    if page == 1:
        return base_url
    query = base_url.split('?')[1] if '?' in base_url else ''
    separator = '&' if query and not query.endswith('&') else ''
    return f"{BASE_DOMAIN}/summary?{query}{separator}page={page}"


def normalize_url(href: str, base_domain: str = BASE_DOMAIN) -> str:
    """normalize url (protocol/domain)"""
    if not href:
        return ""
    if href.startswith('http'):
        return href
    elif href.startswith('//'):
        return 'https:' + href
    elif href.startswith('/'):
        return base_domain + href
    return base_domain + '/' + href.lstrip('/')


def extract_detail_url(link) -> str:
    """extract detail page url"""
    if not link or not link.get('href'):
        return ""
    return normalize_url(link.get('href'))


def parse_table_row(row) -> Optional[Dict]:
    """parse table row"""
    cells = row.find_all(['td', 'th'])
    if len(cells) < 6:
        return None
    
    try:
        company_link = cells[0].find('a')
        company_name = company_link.get_text(strip=True) if company_link else cells[0].get_text(strip=True)
        
        return {
            'COMPANY': company_name or '',
            'CURRENT PARENT': cells[1].get_text(strip=True) if len(cells) > 1 else '',
            'CURRENT PARENT INDUSTRY': cells[2].get_text(strip=True) if len(cells) > 2 else '',
            'OFFENSE CATEGORY': cells[3].get_text(strip=True) if len(cells) > 3 else '',
            'YEAR': cells[4].get_text(strip=True) if len(cells) > 4 else '',
            'PENALTY AMOUNT (USD)': cells[5].get_text(strip=True) if len(cells) > 5 else '',
            'JURISDICTION': 'South Korea',
            'DETAIL_URL': extract_detail_url(company_link)
        }
    except Exception as e:
        logger.warning(f"row parse failed: {e}")
        return None


def parse_search_table(soup: BeautifulSoup) -> List[Dict]:
    """parse search result table"""
    tables = soup.find_all('table')
    if not tables or len(tables) < 2:
        return []
    
    # the second table is the data table
    table = tables[1]
    rows = table.find_all('tr')[1:]  # exclude header
    cases = []
    for row in rows:
        case = parse_table_row(row)
        if case:
            cases.append(case)
    return cases


def parse_detail_page(soup: BeautifulSoup) -> Dict:
    """parse detail page"""
    detail_data = {}
    text = soup.get_text()
    
    # field mapping
    field_mappings = [
        ('U.S. Dollar Equivalent at the Time of the Penalty Announcement', 'PENALTY_AMOUNT_USD'),
        ('Parent at the Time of the Penalty Announcement', 'PARENT_AT_TIME'),
        ('Penalty Amount in Original Currency', 'PENALTY_AMOUNT_ORIGINAL'),
        ('HQ Country of Current Parent', 'HQ_COUNTRY'),
        ('Ownership Structure of Current Parent', 'OWNERSHIP_STRUCTURE'),
        ('Major Industry of Current Parent', 'MAJOR_INDUSTRY'),
        ('Specific Industry of Current Parent', 'SPECIFIC_INDUSTRY'),
        ('Current Parent Company', 'CURRENT_PARENT_COMPANY'),
        ('Penalty Currency', 'PENALTY_CURRENCY'),
        ('Source of Data', 'SOURCE'),
        ('Offense Group', 'OFFENSE_GROUP'),
        ('Offense Category', 'OFFENSE_CATEGORY'),
        ('VTG Record ID', 'VTG_RECORD_ID'),
        ('Company', 'COMPANY'),
        ('Jurisdiction', 'JURISDICTION'),
        ('Region', 'REGION'),
        ('Year', 'YEAR'),
        ('Date', 'DATE'),
        ('Agency', 'AGENCY'),
        ('Description', 'DESCRIPTION'),
    ]
    
    # all field names
    all_field_names = [key for key, _ in field_mappings]
    
    # extract each field
    for field_name, mapped_key in field_mappings:
        if mapped_key in detail_data and detail_data[mapped_key]:
            continue
        
        # "Field Name: Value"
        escaped_field = re.escape(field_name)
        pattern = rf'{escaped_field}:\s*([^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        
        if match:
            value = match.group(1).strip()
            
            # find next field name
            remaining_text = text[match.end():]
            min_pos = len(remaining_text)
            
            for other_field in all_field_names:
                if other_field != field_name:
                    next_pattern = rf'{re.escape(other_field)}:'
                    next_match = re.search(next_pattern, remaining_text, re.IGNORECASE)
                    if next_match and next_match.start() < min_pos:
                        min_pos = next_match.start()
            
            # if next field exists, slice until it; otherwise keep original value
            if min_pos < len(remaining_text):
                # extract longer text
                extended_value = remaining_text[:min_pos].strip()
                if len(extended_value) > len(value):
                    value = extended_value
            elif mapped_key == 'DESCRIPTION':
                # description until specific keywords
                desc_end_pattern = r'(HQ Country|Source of Data|VTG Record|Data Sources|Updates|Menu|Quick Start)'
                desc_end = re.search(desc_end_pattern, remaining_text, re.IGNORECASE)
                if desc_end:
                    value = remaining_text[:desc_end.start()].strip()
            
            # normalize value
            value = value.replace('\n', ' ').replace('\r', ' ').strip()
            # collapse multiple spaces
            value = re.sub(r'\s+', ' ', value)
            
            # exclude empty values
            if value and value not in ['(click here)', '-', 'N/A', 'n/a']:
                # no limit for description, 1000 char limit for others
                if mapped_key == 'DESCRIPTION' or len(value) < 1000:
                    detail_data[mapped_key] = value
    
    # extract source of data link
    if 'SOURCE' not in detail_data or not detail_data.get('SOURCE') or detail_data.get('SOURCE') == '(click here)':
        source_link = soup.find('a', href=True, string=re.compile('click here', re.I))
        if not source_link:
            source_link = soup.find('a', href=True, attrs={'href': re.compile('http')})
        if source_link:
            detail_data['SOURCE'] = normalize_url(source_link.get('href', ''))
    
    return detail_data


def get_case_key(case: Dict) -> tuple:
    """create key for duplicate check"""
    return (
        str(case.get('COMPANY', '')).strip(),
        str(case.get('YEAR', '')).strip(),
        str(case.get('PENALTY AMOUNT (USD)', '')).strip(),
        str(case.get('JURISDICTION', '')).strip()
    )


def parse_date(date_str: str) -> str:
    """convert date format (yyyy-mm-dd)"""
    if not date_str:
        return ""
    date_formats = ['%B %d, %Y', '%Y-%m-%d', '%Y/%m/%d']
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except:
            continue
    return date_str


def extract_fine_amount(value: str) -> str:
    """extract digits from fine amount"""
    if not value:
        return "0"
    cleaned = re.sub(r'[^\d.]', '', str(value))
    try:
        return str(int(float(cleaned)))
    except:
        return "0"


def convert_currency_name_to_code(currency: str) -> str:
    """convert currency name to currency code"""
    if not currency:
        return ""
    currency_map = {
        'south korean won': 'KRW', 'korean won': 'KRW', 'won': 'KRW',
        'us dollar': 'USD', 'dollar': 'USD', 'usd': 'USD',
        'pound': 'GBP', 'british pound': 'GBP', 'gbp': 'GBP',
        'euro': 'EUR', 'eur': 'EUR',
        'singapore dollar': 'SGD', 'sgd': 'SGD',
        'canadian dollar': 'CAD', 'cad': 'CAD',
    }
    currency_lower = currency.lower()
    for key, code in currency_map.items():
        if key in currency_lower:
            return code
    return currency


def remove_duplicates(cases: List[Dict]) -> List[Dict]:
    """remove duplicates"""
    seen = set()
    unique = []
    for case in cases:
        key = get_case_key(case)
        if key not in seen:
            seen.add(key)
            unique.append(case)
    return unique


def convert_to_schema(raw_data: Dict) -> Dict:
    """convert raw data to 13-column schema"""
    # extract fine amount (usd)
    fine_amount_usd = raw_data.get('PENALTY_AMOUNT_USD') or raw_data.get('PENALTY AMOUNT (USD)', '')
    fine_amount_usd = extract_fine_amount(fine_amount_usd)
    
    # extract fine amount (original currency)
    fine_amount_original = raw_data.get('PENALTY_AMOUNT_ORIGINAL', '')
    if fine_amount_original:
        fine_amount_original = re.sub(r'[^\d]', '', str(fine_amount_original))
        if not fine_amount_original:
            fine_amount_original = "0"
    else:
        fine_amount_original = "0"
    
    # convert currency code
    currency = convert_currency_name_to_code(raw_data.get('PENALTY_CURRENCY', ''))
    
    # convert date format
    date_str = parse_date(raw_data.get('DATE', ''))
    
    # company name and violation info
    company = raw_data.get('COMPANY', '') or raw_data.get('CURRENT_PARENT_COMPANY', '')
    violation_type = raw_data.get('OFFENSE_CATEGORY', '') or raw_data.get('OFFENSE CATEGORY', '')
    violation_group = raw_data.get('OFFENSE_GROUP', '')
    
    return {
        'enforcement_id': raw_data.get('VTG_RECORD_ID', ''),
        'country_code': 'KR',
        'company_name': company,
        'sector': raw_data.get('MAJOR_INDUSTRY', ''),
        'violation_group': violation_group,
        'violation_type': violation_type,
        'enforcement_date': date_str,
        'fine_amount_usd': fine_amount_usd,
        'fine_amount_original': fine_amount_original,
        'currency': currency,
        'enforcing_agency': raw_data.get('AGENCY', ''),
        'summary': raw_data.get('DESCRIPTION', ''),
        'source_url': raw_data.get('SOURCE', '')
    }


def log_extracted_info(detail_info: Dict):
    """log extracted info"""
    extracted_fields = []
    if detail_info.get('DATE'):
        extracted_fields.append(f"Date: {detail_info.get('DATE')}")
    if detail_info.get('PENALTY_AMOUNT_USD'):
        extracted_fields.append(f"Fine: {detail_info.get('PENALTY_AMOUNT_USD')}")
    if detail_info.get('AGENCY'):
        extracted_fields.append(f"Agency: {detail_info.get('AGENCY')}")
    if detail_info.get('OFFENSE_CATEGORY'):
        extracted_fields.append(f"Offense: {detail_info.get('OFFENSE_CATEGORY')}")
    if detail_info.get('DESCRIPTION'):
        desc = detail_info.get('DESCRIPTION', '')[:50]
        extracted_fields.append(f"Description: {desc}...")
    
    if extracted_fields:
        logger.info(f" extracted info: {', '.join(extracted_fields)}")


def crawl_detail_pages(session: requests.Session, cases: List[Dict], config: ViolationTrackerConfig):
    """crawl detail page for each case"""
    for case in cases:
        detail_url = case.get('DETAIL_URL', '')
        if not detail_url:
            continue
        
        company_name = case.get('COMPANY', 'Unknown')
        logger.info(f" detail page: {company_name}")
        
        detail_soup = fetch_page(session, detail_url, config)
        if detail_soup:
            detail_info = parse_detail_page(detail_soup)
            case.update(detail_info)
            log_extracted_info(detail_info)
        
        time.sleep(config.delay_between_requests * 0.5)


def filter_new_cases(page_cases: List[Dict], seen_keys: set) -> List[Dict]:
    """return only new cases after removing duplicates"""
    new_cases = []
    for case in page_cases:
        key = get_case_key(case)
        if key not in seen_keys:
            seen_keys.add(key)
            new_cases.append(case)
    return new_cases


def collect_cases(config: ViolationTrackerConfig) -> List[Dict]:
    """collect data"""
    logger.info(f"{config.jurisdiction} data collection start")
    
    session = create_session()
    session.get(config.base_url, timeout=config.timeout)
    
    all_cases = []
    seen_keys = set()
    base_url = build_search_url(config)
    page = 1
    consecutive_empty = 0
    visited_urls = set()
    
    while True:
        current_url = build_page_url(base_url, page)
        
        if current_url in visited_urls:
            logger.warning("already visited url - stop")
            break
        
        visited_urls.add(current_url)
        logger.info(f"page {page} request: {current_url}")
        
        soup = fetch_page(session, current_url, config)
        if not soup:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
            page += 1
            continue
        
        page_cases = parse_search_table(soup)
        if not page_cases:
            consecutive_empty += 1
            if consecutive_empty >= 2:
            logger.info("no data consecutively")
                break
            page += 1
            continue
        
        # remove duplicates
        new_cases = filter_new_cases(page_cases, seen_keys)
        if not new_cases:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                logger.info("only duplicate data consecutively")
                break
        else:
            consecutive_empty = 0
            crawl_detail_pages(session, new_cases, config)
            all_cases.extend(new_cases)
            logger.info(f"page {page}: collected {len(new_cases)} (total {len(all_cases)})")
        
        if len(all_cases) >= TARGET_COUNT:
            logger.info(f"target {TARGET_COUNT} reached")
            break
        
        page += 1
        time.sleep(config.delay_between_requests)
    
    all_cases = remove_duplicates(all_cases)
    converted_cases = [convert_to_schema(case) for case in all_cases]
    
    logger.info(f"total collected: {len(converted_cases)}")
    return converted_cases


def save_to_csv(data: List[Dict], config: ViolationTrackerConfig, country_code: str):
    """save to csv"""
    output_dir = Path(__file__).parent / f"{country_code}_data_Sprt"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'violation_tracker_{country_code}_{timestamp}.csv'
    
    with open(str(output_file), 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=config.schema_columns)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"csv saved: {output_file} ({len(data)})")


def main():
    """main"""
    config = ViolationTrackerConfig(jurisdiction="South Korea")
    country_code = "South_korea"
    
    logger.info("south korea data collection start")
    output_dir = Path(__file__).parent / f"{country_code}_data_Sprt"
    output_dir.mkdir(exist_ok=True, parents=True)
    temp_file = output_dir / f'violation_tracker_{country_code}_temp.csv'
    
    all_data = []
    if temp_file.exists():
        try:
            with open(str(temp_file), 'r', encoding='utf-8-sig') as f:
                all_data = list(csv.DictReader(f))
                logger.info(f"temp file recovered: {len(all_data)}")
        except Exception as e:
            logger.warning(f"temp file load failed: {e}")
    
    try:
        new_data = collect_cases(config)
        all_data = all_data + new_data if all_data else new_data
        
        save_to_csv(all_data, config, country_code)
        
        logger.info(f"country: {config.jurisdiction}")
        logger.info(f"total cases: {len(all_data)}")
        
        if temp_file.exists():
            temp_file.unlink()
            logger.info("temp file deleted")
        
        logger.info("done")
    
    except Exception as e:
        logger.error(f"error occurred: {e}")
        if all_data:
            try:
                with open(str(temp_file), 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=config.schema_columns)
                    writer.writeheader()
                    writer.writerows(all_data)
                logger.info(f"temp file saved: {temp_file} ({len(all_data)})")
            except Exception as save_error:
                logger.error(f"temp save failed: {save_error}")
        raise


if __name__ == "__main__":
    main()
