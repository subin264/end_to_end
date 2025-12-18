#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ICO UK Enforcement Web Scraper (Playwright)

On the site https://ico.org.uk/action-weve-taken/enforcement
Web scraping enforcement case data from the UK ICO.
"""

import pandas as pd
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import re
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page

OUTPUT_DIR = Path("/Users/baesubin/Desktop/데이터 수집_end_to_end/uk_data_set_2/webscraping_row_data_uk_de")
COLUMNS_ORDER = [
    'Company', 'Date', 'Type', 'Sector', 'Summary',
    'Fine_Amount', 'PDF_URL',
    'Source_URL', 'Country', 'Authority'
]

@dataclass
class Config:
    base_url: str = "https://ico.org.uk/action-weve-taken/enforcement"
    timeout: int = 30000
    delay: float = 1.0
    output_dir: Path = None
    batch_size: int = 1000
    
    def __post_init__(self):
        if self.output_dir is None:
            OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
            self.output_dir = OUTPUT_DIR

def setup_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    
    file_handler = logging.FileHandler(
        OUTPUT_DIR / f"ico_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger

logger = setup_logging()

async def apply_sector_filter(page: Page, sector: str):
    try:
        checkbox = await page.query_selector(f"label:has-text('{sector}') input")
        if checkbox:
            is_checked = await checkbox.is_checked()
            if not is_checked:
                await checkbox.click()
                await page.wait_for_timeout(1000)  # 필터 적용 대기
                return True
        else:
            logger.warning(f"섹터 체크박스를 찾을 수 없음: {sector}")
    except Exception as e:
        logger.warning(f"섹터 필터 적용 실패 ({sector}): {e}")
    return False

async def collect_case_links(page: Page, config: Config, sectors: List[str] = None) -> List[str]:
    all_links = []
    page_num = 1
    
    try:
        await page.goto(config.base_url, wait_until='networkidle', timeout=config.timeout)
        await page.wait_for_timeout(3000)
        await handle_cookie_banner(page)
        
        if sectors:
            for sector in sectors:
                await apply_sector_filter(page, sector)
            await page.wait_for_timeout(2000)  # 필터 적용 후 페이지 로딩 대기
        
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            try:
                links = await page.query_selector_all("ul.list-none li a.block.group, a[href*='/action-weve-taken/enforcement/']")
                
                for link in links:
                    href = await link.get_attribute('href')
                    if href and '/enforcement/' in href and href != '/action-weve-taken/enforcement/':
                        full_url = href if href.startswith('http') else f"https://ico.org.uk{href}"
                        if full_url not in all_links:
                            all_links.append(full_url)
                
            except Exception as e:
                logger.warning(f"페이지 {page_num} 링크 수집 실패: {e}")
                break
            
            next_button = None
            selectors = [
                "a:has-text('Next')",
                "button:has-text('Next')",
                "a[aria-label='Next page']",
                "a[aria-label='Next']",
                "button[aria-label='Next page']",
                ".pagination a:has-text('Next')",
                "nav a:has-text('Next')",
                "[aria-label*='Next']",
                "a[title*='Next']"
            ]
            
            for selector in selectors:
                try:
                    next_button = await page.query_selector(selector)
                    if next_button:
                        is_visible = await next_button.is_visible()
                        if is_visible:
                            break
                        next_button = None
                except:
                    continue
            
            if not next_button:
                break
            
            try:
                is_disabled = await next_button.get_attribute('aria-disabled')
                class_attr = await next_button.get_attribute('class') or ""
                
                if is_disabled == 'true' or 'disabled' in class_attr.lower():
                    break
            except:
                pass
            
            try:
                await next_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                await next_button.click()
                await page.wait_for_timeout(4000)  # 페이지 로딩 대기
                await page.wait_for_load_state('networkidle', timeout=10000)
                page_num += 1
            except Exception as e:
                logger.warning(f"다음 페이지 클릭 실패: {e}")
                break
                
    except Exception as e:
        logger.error(f"케이스 링크 수집 중 오류: {e}")
    
    logger.info(f"총 {len(all_links)}개 케이스 링크 수집 완료")
    return all_links


async def handle_cookie_banner(page: Page):
    try:
        cookie_btn = await page.query_selector("button:has-text('Accept'), button:has-text('Accept all')")
        if cookie_btn:
            await cookie_btn.click()
            await page.wait_for_timeout(1000)
    except:
        pass


def extract_field_by_label(text: str, label: str) -> str:
    match = re.search(rf'{label}[:\s]+([^\n]+)', text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_fine_amount(text: str) -> str:
    patterns = [
        (r'£\s*(\d+(?:\.\d+)?)\s*(?:million|m)\b', lambda m: f"£{int(float(m.group(1)) * 1_000_000):,}"),
        (r'£\s*(\d{1,3}(?:,\d{3})+)', lambda m: f"£{m.group(1)}"),
        (r'£\s*(\d{4,})', lambda m: f"£{int(m.group(1)):,}")
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return formatter(match)
    return ""


def default_sectors() -> List[str]:
    return [
        "Finance insurance and credit",
        "General business",
        "Health",
        "Marketing",
        "Media",
        "Online technology and telecoms",
        "Retail and manufacture",
        "Social care",
        "Transport and leisure",
        "Utilities",
    ]


def normalize_pdf_url(pdf_url: str) -> str:
    if not pdf_url:
        return ""
    
    if pdf_url.startswith('file://'):
        return pdf_url.replace('file://', 'https://ico.org.uk')
    elif pdf_url.startswith('/'):
        return f"https://ico.org.uk{pdf_url}"
    elif pdf_url.startswith('https://'):
        return pdf_url
    else:
        return f"https://ico.org.uk/{pdf_url}"


async def extract_basic_info(page: Page, url: str) -> Optional[Dict]:
    try:
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)
        await handle_cookie_banner(page)
        
        company_elem = await page.query_selector("main h1")
        if not company_elem:
            logger.warning(f"회사명 없음: {url}")
            return None
        
        company = (await company_elem.inner_text()).strip()
        
        body_elem = await page.query_selector("body")
        body_text = (await body_elem.inner_text()).strip() if body_elem else ""
        
        date = extract_field_by_label(body_text, 'Date') or re.search(r'(\d{1,2}\s+\w+\s+\d{4})', body_text)
        date = date.group(1).strip() if isinstance(date, re.Match) else date
        
        type_info = extract_field_by_label(body_text, 'Type')
        sector = extract_field_by_label(body_text, 'Sector')
        fine_amount = extract_fine_amount(body_text)
        
        summary = ""
        try:
            summary_elem = await page.query_selector("main p, .content p")
            if summary_elem:
                summary = (await summary_elem.inner_text()).strip()[:500]
        except:
            pass
        
        pdf_url = ""
        try:
            pdf_elem = await page.query_selector("a[href$='.pdf']")
            if pdf_elem:
                raw_url = await pdf_elem.get_attribute('href')
                pdf_url = normalize_pdf_url(raw_url) if raw_url else ""
        except:
            pass
        
        return {
            'Company': company,
            'Date': date,
            'Type': type_info,
            'Sector': sector,
            'Summary': summary,
            'Fine_Amount': fine_amount,
            'PDF_URL': pdf_url,
            'Source_URL': url,
            'Country': 'United Kingdom',
            'Authority': 'ICO'
        }
        
    except Exception as e:
        logger.error(f"케이스 페이지 파싱 실패 {url}: {e}")
        return None

def get_processed_urls(output_dir: Path) -> set:
    processed_urls = set()
    batch_files = list(output_dir.glob("5_ico_raw_data_part*.csv"))
    
    for batch_file in batch_files:
        try:
            df = pd.read_csv(batch_file, encoding='utf-8-sig')
            if 'Source_URL' in df.columns:
                processed_urls.update(df['Source_URL'].dropna().astype(str).tolist())
        except Exception as e:
            logger.warning(f"기존 파일 읽기 실패 {batch_file}: {e}")
    
    logger.info(f"이미 처리된 url: {len(processed_urls)}개")
    return processed_urls


def prepare_dataframe(data: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    existing_columns = [col for col in COLUMNS_ORDER if col in df.columns]
    return df[existing_columns]


def save_batch_csv(data: List[Dict], batch_num: int, config: Config) -> Optional[Path]:
    if not data:
        return None
    
    df = prepare_dataframe(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    part_str = f"part{batch_num:02d}"
    filename = config.output_dir / f"5_ico_raw_data_{part_str}_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    logger.info(f"배치 저장 완료: {filename}")
    return filename


def merge_batch_files(batch_files: List[Path], config: Config) -> Optional[Path]:
    if not batch_files:
        return None
    
    all_dfs = []
    for batch_file in batch_files:
        try:
            df = pd.read_csv(batch_file, encoding='utf-8-sig')
            all_dfs.append(df)
            logger.info(f"배치 파일 읽기: {batch_file} ({len(df)}건)")
        except Exception as e:
            logger.error(f"배치 파일 읽기 실패 {batch_file}: {e}")
    
    if not all_dfs:
        return None
    
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    before_count = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['Source_URL'], keep='first')
    after_count = len(merged_df)
    
    if before_count != after_count:
        logger.info(f"중복 제거: {before_count}건 → {after_count}건")
    
    existing_columns = [col for col in COLUMNS_ORDER if col in merged_df.columns]
    other_columns = [col for col in merged_df.columns if col not in existing_columns]
    merged_df = merged_df[existing_columns + other_columns]
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = config.output_dir / f"5_ico_raw_data_merged_{timestamp}.csv"
    merged_df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    logger.info(f"병합 완료: {filename}")
    return filename

async def process_all_cases(page: Page, case_links: List[str], config: Config) -> List[Path]:
    processed_urls = get_processed_urls(config.output_dir)
    
    all_data = []
    batch_files = []
    batch_num = 1

    total_links = len(case_links)
    for idx, link in enumerate(case_links, 1):
        if link in processed_urls:
            continue

        case_data = await extract_basic_info(page, link)
        if case_data:
            all_data.append(case_data)

        if len(all_data) >= config.batch_size:
            batch_file = save_batch_csv(all_data, batch_num, config)
            if batch_file:
                batch_files.append(batch_file)
            all_data = []
            batch_num += 1

        if idx < total_links:
            await asyncio.sleep(config.delay)
    
    if all_data:
        batch_file = save_batch_csv(all_data, batch_num, config)
        if batch_file:
            batch_files.append(batch_file)
    
    return batch_files

async def scrape_ico_data(sectors: List[str] = None):
    config = Config()
    
    if sectors is None:
        sectors = default_sectors()
    
    try:
        logger.info("ico uk enforcement scraping start (playwright)")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                case_links = await collect_case_links(page, config, sectors=sectors)
                
                if not case_links:
                    logger.warning("no case links collected")
                    return
                
                logger.info(f"total cases: {len(case_links)}")
                batch_files = await process_all_cases(page, case_links, config)
                
                if batch_files:
                    logger.info(f"scraping done: {len(batch_files)} batch files")
                    merged_file = merge_batch_files(batch_files, config)
                    if merged_file:
                        logger.info(f"merged file: {merged_file}")
                else:
                    logger.warning("no data collected")
                    
            finally:
                await browser.close()
                
    except Exception as e:
        logger.error(f"scraping error: {e}", exc_info=True)


def main():
    sectors = default_sectors()
    asyncio.run(scrape_ico_data(sectors=sectors))


if __name__ == "__main__":
    main()
