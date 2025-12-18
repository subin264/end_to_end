#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMS GDPR Enforcement Tracker Scraper

Scraping GDPR fine data from enforcementtracker.com
Return the original table structure as is (maintain original column names)
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import stat


@dataclass
class Config:
    """scraper config"""
    base_url: str = "https://www.enforcementtracker.com"
    target_country: str = None  # if none, collect all countries
    timeout: int = 20
    retry_count: int = 3
    delay: float = 0.5
    output_dir: Path = None
    
    def __post_init__(self):
        if self.output_dir is None:
            default_dir = Path(__file__).parent / "webscraping_row_data_uk_de"
            default_dir.mkdir(exist_ok=True)
            self.output_dir = default_dir


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / f"enforcement_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
    ],
    force=True
)
logger = logging.getLogger(__name__)


def get_driver():
    """create chrome webdriver"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)
        return driver
    except Exception:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            
            if os.path.exists(driver_path):
                os.chmod(driver_path, 0o755)
            
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(5)
            return driver
        except Exception as e:
            logger.error(f"chromedriver creation failed: {e}")
            raise


def build_target_url(config: Config) -> str:
    if config.target_country:
        return f"{config.base_url}/?country={config.target_country.replace(' ', '%20')}"
    return config.base_url


def wait_for_penalties_table(driver, timeout: int) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, "penalties"))
    )
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#penalties tbody tr"))
    )
    time.sleep(0.5)


def extract_headers(driver) -> List[str]:
    """extract table headers"""
    try:
        thead = driver.find_element(By.CSS_SELECTOR, "#penalties thead")
        th_list = thead.find_elements(By.TAG_NAME, "th")
        headers = []
        
        for th in th_list:
            text = th.text.strip()
            if text and text not in ['', '↑', '↓', '⇅']:
                headers.append(text)
            elif not text:
                headers.append(f"Column_{len(headers) + 1}")
        
        try:
            first_row = driver.find_element(By.CSS_SELECTOR, "#penalties tbody tr[role='row']")
            cells = first_row.find_elements(By.TAG_NAME, "td")
            actual_count = len(cells)
            
            if len(headers) < actual_count:
                logger.warning(f"header shortage: {len(headers)} < actual {actual_count}")
                for i in range(len(headers), actual_count):
                    headers.append(f"Column_{i + 1}")
            elif len(headers) > actual_count:
                logger.warning(f"header overflow: {len(headers)} > actual {actual_count}")
                headers = headers[:actual_count]
        except:
            pass
        
        return headers
    except Exception as e:
        logger.error(f"header extraction failed: {e}")
        return []


def extract_row_data(row_element, driver) -> List[str]:
    """extract row data"""
    try:
        cells = row_element.find_elements(By.TAG_NAME, "td")
        row_data = []
        
        for cell in cells:
            try:
                text = driver.execute_script("""
                    var cell = arguments[0];
                    var text = cell.innerText || cell.textContent || '';
                    
                    var img = cell.querySelector('img');
                    if (img && img.alt) {
                        text = (text + ' ' + img.alt).trim();
                    }
                    
                    var link = cell.querySelector('a');
                    if (link && link.href) {
                        text = text ? (text + ' | ' + link.href) : link.href;
                    }
                    
                    return text.trim();
                """, cell)
                row_data.append(text or "")
            except:
                try:
                    text = cell.text.strip()
                    
                    img = cell.find_element(By.TAG_NAME, "img")
                    if img:
                        alt = img.get_attribute("alt") or ""
                        if alt:
                            text = f"{text} {alt}".strip()
                except:
                    pass
                
                try:
                    link = cell.find_element(By.TAG_NAME, "a")
                    if link:
                        href = link.get_attribute("href") or ""
                        if href:
                            text = f"{text} | {href}" if text else href
                except:
                    pass
                
                row_data.append(text or "")
        
        return row_data
    except Exception as e:
        logger.warning(f"row data extraction failed: {e}")
        return []


def scrape_current_page(driver, config: Config) -> Tuple[List[str], List[List[str]]]:
    """extract current page data"""
    headers = extract_headers(driver)
    if not headers:
        return [], []
    
    rows_data = []
    try:
        tbody = driver.find_element(By.CSS_SELECTOR, "#penalties tbody")
        rows = tbody.find_elements(By.CSS_SELECTOR, "tr[role='row']")
        for idx, row in enumerate(rows, 1):
            try:
                row_data = extract_row_data(row, driver)
                if row_data:
                    rows_data.append(row_data)
            except Exception as e:
                logger.warning(f"row {idx} failed: {e}")
                rows_data.append([""] * len(headers))
    except Exception as e:
        logger.error(f"page extraction failed: {e}")
    
    return headers, rows_data


def has_next_page(driver) -> bool:
    """check if next page exists"""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "#penalties_next")
        return "disabled" not in next_button.get_attribute("class")
    except:
        return False


def go_to_next_page(driver):
    """go to next page"""
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "#penalties_next")
        if "disabled" not in next_button.get_attribute("class"):
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#penalties tbody tr")) > 0
            )
            return True
    except Exception as e:
        logger.warning(f"next page navigation failed: {e}")
        return False


def summarize_country_counts(headers: List[str], rows: List[List[str]]) -> None:
    if not headers or not rows:
        return
    country_idx = next((i for i, h in enumerate(headers) if 'country' in h.lower()), None)
    if country_idx is None:
        return
    country_counts = {}
    for row in rows:
        if len(row) > country_idx and row[country_idx]:
            country = row[country_idx].strip()
            country_counts[country] = country_counts.get(country, 0) + 1
    _ = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]


def scrape_all_fines(config: Config = None) -> Optional[Tuple[List[str], List[List[str]]]]:
    """scrape gdpr fine data"""
    if config is None:
        config = Config()
    
    if config.target_country:
        logger.info(f"scraping start: {config.target_country}")
    else:
        logger.info("scraping start: all countries")
    
    url = build_target_url(config)
    driver = get_driver()
    
    try:
        driver.get(url)
        
        wait_for_penalties_table(driver, config.timeout)
        
        all_headers = []
        all_rows = []
        page = 0
        
        while True:
            page += 1
            
            headers, rows = scrape_current_page(driver, config)
            
            if not all_headers and headers:
                all_headers = headers
            
            if rows:
                all_rows.extend(rows)
            
            if not has_next_page(driver):
                break
            
            if not go_to_next_page(driver):
                break
            
            time.sleep(0.3)
        
        summarize_country_counts(all_headers, all_rows)
        
        return (all_headers, all_rows) if all_rows else None
    
    except Exception as e:
        logger.error(f"scraping failed: {e}", exc_info=True)
        return None
    
    finally:
        driver.quit()


def save_to_csv(headers: List[str], rows: List[List[str]], config: Config) -> Optional[Path]:
    """save to csv"""
    if not headers or not rows:
        logger.warning("no data to save")
        return None
    
    col_count = len(headers)
    fixed_rows = []
    
    for row in rows:
        if len(row) > col_count:
            row = row[:col_count]
        elif len(row) < col_count:
            row = row + [''] * (col_count - len(row))
        fixed_rows.append(row)
    
    df = pd.DataFrame(fixed_rows, columns=headers)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if config.target_country:
        country_name = config.target_country.replace(' ', '_').lower()
        filename = config.output_dir / f"5_enforcement_tracker_{country_name}_{timestamp}.csv"
    else:
        filename = config.output_dir / f"5_enforcement_tracker_all_countries_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    logger.info(f"save completed: {filename}")
    return filename


def main():
    """main"""
    config = Config()
    config.target_country = "Germany"
    
    result = scrape_all_fines(config)
    
    if result:
        headers, rows = result
        logger.info(f"done: {len(headers)} columns, {len(rows)} rows")
        
        saved_file = save_to_csv(headers, rows, config)
        if saved_file:
            logger.info(f"file: {saved_file}")
        
        return result
    else:
        logger.warning("no data")
        return None


if __name__ == "__main__":
    main()
