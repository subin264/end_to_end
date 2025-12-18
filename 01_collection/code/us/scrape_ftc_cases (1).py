#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ftc privacy & security enforcement cases scraper.

collects case detail pages from ftc "cases & proceedings" listing pages and exports a csv.

inputs:
- `FTCConfig.privacy_security_tag_url` (start url for listing pagination)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import time
from dataclasses import dataclass


 

@dataclass
class FTCConfig:
    """ftc scraper config"""
    
    base_url: str = "https://www.ftc.gov"
    
    # search results page
    privacy_security_tag_url: str = (
        "https://www.ftc.gov/legal-library/browse/cases-proceedings?sort_by=search_api_relevance&items_per_page=20&search=driver+information&field_competition_topics=All&field_consumer_protection_topics=All&field_case_action_type%5BFederal%5D=Federal&field_case_action_type%5BAdministrative%5D=Administrative&field_federal_court=All&field_industry=All&field_case_status=All&field_enforcement_type=All&search_matter_number=&search_civil_action_number=&start_date=&end_date=")
    
    request_timeout: int = 15
    retry_count: int = 3
    delay_between_requests: float = 2.0
    
    headers: Dict[str, str] = None
    
    # 16-column schema (enforcement.csv)
    schema_columns: List[str] = None
    
    # ai keywords
    ai_keywords: List[str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )
            }
        
        if self.schema_columns is None:
            self.schema_columns = [
                'enforcement_id', 'country_code', 'regulation_id',
                'regulation_name', 'case_name', 'company_name',
                'sector', 'violation_type', 'violation_date',
                'enforcement_date', 'fine_amount_usd', 'settlement_type',
                'ai_related', 'current_status', 'source_url', 'summary',
                'issue_description', 'document_urls', 'document_types',
                'violated_laws', 'tags_raw',
            ]
        
        if self.ai_keywords is None:
            self.ai_keywords = [
                'artificial intelligence', 'machine learning', 'deep learning',
                'neural network', 'algorithm', 'automated decision', 'ai',
                'predictive analytics', 'data mining', 'facial recognition',
                'biometric', 'computer vision', 'natural language processing',
                'chatbot', 'recommendation system', 'personalization engine'
            ]


 

def setup_logger(name: str = __name__) -> logging.Logger:
    """logger setup"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger
    
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


 

def fetch_page_with_retry(
    url: str,
    config: FTCConfig
) -> Optional[BeautifulSoup]:
    """fetch a page with retries"""
    
    for attempt in range(1, config.retry_count + 1):
        try:
            response = requests.get(
                url,
                headers=config.headers,
                timeout=config.request_timeout
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
            
        except Exception as e:
            logger.warning(f"attempt {attempt}/{config.retry_count} failed: {e}")
            if attempt < config.retry_count:
                time.sleep(2)
    
    logger.error(f"final failure: {url}")
    return None


 

def extract_case_links(
    tag_url: str,
    config: FTCConfig,
    max_pages: int = 20,
) -> List[str]:
    """extract case links with pagination safety limit"""
    
    all_links: Set[str] = set()
    
    for page in range(max_pages):
        if page == 0:
            page_url = tag_url
        else:
            separator = "&" if "?" in tag_url else "?"
            page_url = f"{tag_url}{separator}page={page}"
        
        logger.info(f"open list page: page={page}")
        soup = fetch_page_with_retry(page_url, config)
        
        if not soup:
            logger.warning(f"stop pagination due to page load failure (page={page})")
            break
        
        before_count = len(all_links)
        
        page_links: List[str] = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if not href:
                continue
            
            if '/legal-library/browse/cases-proceedings/' in href:
                if href.startswith('/'):
                    full_url = config.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = config.base_url + '/' + href.lstrip('/')
                
                if '?' in full_url:
                    full_url = full_url.split('?')[0]
                
                if 'banned-debt-collectors' not in full_url.lower():
                    page_links.append(full_url)
                    all_links.add(full_url)
        
        after_count = len(all_links)
        new_count = after_count - before_count
        
        logger.info(f"found: +{new_count} (total {after_count})")
        
        if new_count == 0:
            logger.info(f"stop pagination due to no new links (page={page})")
            break
    
    case_links = list(all_links)
    logger.info(f"total cases: {len(case_links)}")
    return case_links


 

def parse_case_page(
    url: str,
    config: FTCConfig
) -> Optional[Dict]:
    """parse a case detail page"""
    
    soup = fetch_page_with_retry(url, config)
    if not soup:
        return None
    
    try:
        h1 = soup.find('h1')
        if h1:
            company_name = h1.get_text(strip=True)
            company_name = re.sub(r',?\s*In the Matter of.*', '', company_name, flags=re.IGNORECASE)
        else:
            company_name = "Unknown"
        
        tags = []
        tag_links = soup.find_all('a', href=re.compile(r'/enforcement/cases-proceedings/terms/'))
        for tag in tag_links:
            tags.append(tag.get_text(strip=True))
        
        violation_type = ', '.join(tags) if tags else "Unknown"
        
        page_text = soup.get_text()
        
        # Last Updated
        last_updated_match = re.search(r'Last Updated:\s*(.+?)(?:\n|$)', page_text)
        last_updated = last_updated_match.group(1).strip() if last_updated_match else ""
        
        # Case Status
        case_status_match = re.search(r'Case Status:\s*(.+?)(?:\n|$)', page_text)
        case_status = case_status_match.group(1).strip() if case_status_match else "Unknown"
        
        # FTC Matter/File Number
        case_number_match = re.search(r'FTC Matter/File Number:\s*(.+?)(?:\n|$)', page_text)
        case_number = case_number_match.group(1).strip().replace(' ', '') if case_number_match else ""
        
        # Enforcement Type
        enforcement_type_match = re.search(r'Enforcement Type:\s*(.+?)(?:\n|$)', page_text)
        enforcement_type = enforcement_type_match.group(1).strip() if enforcement_type_match else ""
        
        # press release link (optional)
        press_release_url = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/news-events/news/press-releases/' in href:
                press_release_url = config.base_url + href if href.startswith('/') else href
                break
        
        # 5. Case Summary
        summary_div = soup.find('div', class_='field--name-field-case-summary')
        if summary_div:
            summary = summary_div.get_text(strip=True)[:500]
        else:
            summary = ""
        
        # fine amount (case page + press release + consent/final order)
        fine_amount = extract_fine_amount(page_text)
        press_soup = None
        
        if fine_amount == 0 and press_release_url:
            press_soup = fetch_page_with_retry(press_release_url, config)
            if press_soup:
                press_text = press_soup.get_text()
                fine_amount = extract_fine_amount(press_text)

                if fine_amount == 0:
                    consent_urls = []
                    for a in press_soup.find_all('a', href=True):
                        href = a['href']
                        if '/sites/default/files/documents/cases/' in href or href.endswith(('.htm', '.html', '.pdf')):
                            if href.startswith('http'):
                                full_url = href
                            else:
                                full_url = config.base_url + href
                            consent_urls.append(full_url)
                    
                    # de-dup and cap to avoid too many requests
                    seen: Set[str] = set()
                    filtered_consent_urls = []
                    for cu in consent_urls:
                        if cu not in seen:
                            seen.add(cu)
                            filtered_consent_urls.append(cu)
                        if len(filtered_consent_urls) >= 3:
                            break
                    
                    for consent_url in filtered_consent_urls:
                        logger.info(f"retry fine from consent/order: {consent_url}")
                        consent_soup = fetch_page_with_retry(consent_url, config)
                        if not consent_soup:
                            continue
                        consent_text = consent_soup.get_text()
                        amount_from_consent = extract_fine_amount(consent_text)
                        if amount_from_consent > 0:
                            fine_amount = amount_from_consent
                            logger.info(f"fine found in consent document: {fine_amount} usd")
                            break

        # document metadata (case page + press release)
        document_urls: List[str] = []
        document_types: List[str] = []

        def add_document(href: str, source: str) -> None:
            """tag document url and type."""
            if not href:
                return
            if href.startswith('http'):
                full_url = href
            else:
                full_url = config.base_url + href

            if full_url in document_urls:
                return

            doc_type = []
            href_lower = href.lower()
            if 'consent' in href_lower or 'order' in href_lower:
                doc_type.append('order_or_consent')
            if 'complaint' in href_lower:
                doc_type.append('complaint')
            if href_lower.endswith('.pdf'):
                doc_type.append('pdf')
            if href_lower.endswith(('.htm', '.html')):
                doc_type.append('html')
            if '/documents/cases/' in href_lower:
                doc_type.append('case_document')
            if not doc_type:
                doc_type.append('other')
            doc_type.append(source)

            document_urls.append(full_url)
            document_types.append('|'.join(doc_type))

        # collect document links from the case page
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/documents/cases/' in href or href.endswith(('.pdf', '.htm', '.html')):
                add_document(href, 'case')

        # collect document links from the press release page
        if press_soup:
            for link in press_soup.find_all('a', href=True):
                href = link['href']
                if '/documents/cases/' in href or href.endswith(('.pdf', '.htm', '.html')):
                    add_document(href, 'press')

        # issue_description and violated_laws
        issue_description = ""
        violated_laws_set: Set[str] = set()

        # (1) extract issue sentences from the press release
        if press_soup:
            try:
                press_text_for_issue = press_text.strip()
                sentences = re.split(r'(?<=[.!?])\s+', press_text_for_issue)
                candidate_sentences: List[str] = []
                for s in sentences:
                    s_stripped = s.strip()
                    if not s_stripped:
                        continue
                    if len(s_stripped) < 40:
                        continue
                    if re.search(r'\b(alleges?|charged?|violated?|violation|unlawful|illegal)\b', s_stripped, re.IGNORECASE):
                        candidate_sentences.append(s_stripped)
                    if len(candidate_sentences) >= 2:
                        break
                if candidate_sentences:
                    issue_description = ' '.join(candidate_sentences)[:500]
            except Exception as e:
                logger.warning(f"warning while extracting issue_description from press release: {e}")

        # (2) simple law name extraction
        LAW_KEYWORDS = [
            'children\'s online privacy protection act',
            'coppa',
            'ftc act',
            'section 5 of the federal trade commission act',
            'gramm-leach-bliley act',
            'glba',
            'fair credit reporting act',
            'fcra',
            'health insurance portability and accountability act',
            'hipaa',
            'red flags rule',
            'safeguards rule',
        ]
        def collect_violated_laws(text: str) -> None:
            text_lower = text.lower()
            for law in LAW_KEYWORDS:
                if law in text_lower:
                    violated_laws_set.add(law)

        collect_violated_laws(page_text)
        if press_soup:
            collect_violated_laws(press_text)

        # (3) fallback to case summary prefix
        if not issue_description and summary:
            issue_description = summary[:500]

        violated_laws = '; '.join(sorted(violated_laws_set)) if violated_laws_set else ""
        
        # ai-related flag
        is_ai_related = check_ai_keywords(summary + ' ' + violation_type, config.ai_keywords)
        
        # structure output record
        case_data = {
            'enforcement_id': f"US_FTC_{case_number}" if case_number else f"US_FTC_UNKNOWN_{int(time.time())}",
            'country_code': 'US',
            'regulation_id': 'US_FTC',
            'regulation_name': 'Federal Trade Commission Act',
            'case_name': h1.get_text(strip=True) if h1 else "Unknown",
            'company_name': company_name,
            'sector': 'Unknown',
            'violation_type': violation_type,
            'violation_date': '',
            'enforcement_date': last_updated,
            'fine_amount_usd': fine_amount,
            'settlement_type': enforcement_type,
            'ai_related': 1 if is_ai_related else 0,
            'current_status': case_status,
            'source_url': url,
            'summary': summary,
            'issue_description': issue_description,
            'document_urls': '; '.join(document_urls),
            'document_types': '; '.join(document_types),
            'violated_laws': violated_laws,
            'tags_raw': ', '.join(tags) if tags else '',
        }
        
        return case_data
        
    except Exception as e:
        logger.error(f"case parse failed {url}: {e}")
        return None


def extract_fine_amount(text: str) -> int:
    """extract fine amount from text"""
    
    patterns = [
        r'\$([0-9,]+(?:\.[0-9]+)?)\s*million',
        r'\$([0-9,]+(?:\.[0-9]+)?)\s*billion',
        r'pay\s*\$([0-9,]+)',
        r'penalty\s+of\s*\$([0-9,]+)',
        r'fine\s+of\s*\$([0-9,]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            amount = float(amount_str)
            
            if 'million' in match.group(0).lower():
                return int(amount * 1_000_000)
            elif 'billion' in match.group(0).lower():
                return int(amount * 1_000_000_000)
            else:
                return int(amount)
    
    return 0


def check_ai_keywords(text: str, keywords: List[str]) -> bool:
    """ai keyword check"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


 

def scrape_ftc_cases(config: FTCConfig, max_cases: Optional[int] = None) -> pd.DataFrame:
    """main scraper (max_cases is for quick test runs)"""
    
    logger.info("=" * 60)
    logger.info("FTC Privacy & Security Cases Scraper")
    logger.info("=" * 60)
    
    case_links = extract_case_links(
        config.privacy_security_tag_url,
        config,
        max_pages=20,
    )
    
    if not case_links:
        logger.error("no case links found")
        return pd.DataFrame(columns=config.schema_columns)
    
    results = []
    
    if max_cases is not None:
        target_links = case_links[:max_cases]
        logger.info(f"test mode: max_cases={max_cases} (total links={len(case_links)})")
    else:
        target_links = case_links
    
    for i, url in enumerate(target_links, 1):
        logger.info(f"[{i}/{len(target_links)}] scraping: {url}")
        
        case_data = parse_case_page(url, config)
        if case_data:
            results.append(case_data)
            logger.info(f" ok {case_data['company_name']}")
        else:
            logger.warning("failed to parse")
        
        if i < len(target_links):
            time.sleep(config.delay_between_requests)
    
    df = pd.DataFrame(results, columns=config.schema_columns)
    
    logger.info("=" * 60)
    logger.info(f"total collected: {len(df)}")
    if "ai_related" in df.columns:
        logger.info(f"ai-related: {int(df['ai_related'].sum())}")
    logger.info("=" * 60)
    
    return df


 

def main():
    """entry point"""
    
    
    config = FTCConfig()
    
    # scrape (no max_cases limit)
    df = scrape_ftc_cases(config, max_cases=None)
    
    # keep output folder name as-is to preserve local workflow
    output_dir = Path(__file__).parent / "scrape_결과저장"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"ftc_cases_{timestamp}.csv"
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"saved: {output_file}")
    
    return df


if __name__ == "__main__":
    main()
