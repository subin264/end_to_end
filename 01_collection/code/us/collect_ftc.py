"""
fda data dashboard api - compliance actions collection
Enforcement: Warning Letters, Injunctions, Seizures
"""

import requests
import pandas as pd
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FDAConfig:
    API_BASE = "https://api-datadashboard.fda.gov/v1"
    ENDPOINT = "/complianceactions"
    
    AUTH_USER = os.getenv("FDA_AUTH_USER")
    AUTH_KEY = os.getenv("FDA_AUTH_KEY")
    
    TIMEOUT = 60
    MAX_ROWS = 5000  # fda api max rows
    OUTPUT_DIR = Path("./fda_enforcement")


def fetch_compliance_actions(
    product_types: List[str] = None,
    action_types: List[str] = None,
    start_date: str = "2020-01-01",
    end_date: str = None
) -> pd.DataFrame:
    
    url = f"{FDAConfig.API_BASE}{FDAConfig.ENDPOINT}"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization-User': FDAConfig.AUTH_USER,
        'Authorization-Key': FDAConfig.AUTH_KEY
    }

    if not FDAConfig.AUTH_USER or not FDAConfig.AUTH_KEY:
        raise RuntimeError("missing auth: set FDA_AUTH_USER and FDA_AUTH_KEY environment variables")
    
    filters = {
        "ActionTakenDateFrom": [start_date]
    }
    if end_date:
        filters["ActionTakenDateTo"] = [end_date]
    if product_types:
        filters["ProductType"] = product_types
    if action_types:
        filters["ActionType"] = action_types
    
    body = {
        "filters": filters,
        "columns": [],  # empty list means all columns
        "sort": "ActionTakenDate",
        "sortorder": "DESC",
        "rows": FDAConfig.MAX_ROWS,
        "start": 1,
        "returntotalcount": True
    }
    
    logger.info(f"fda api request: {product_types or 'All'} / {action_types or 'All'}")
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=FDAConfig.TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # fda api returns 400 for success
        if data.get('statuscode') != 400:
            logger.error(f"api error: {data.get('message')}")
            return pd.DataFrame()
        
        total = data.get('totalrecordcount', 0)
        results = data.get('result', [])
        
        logger.info(f"collected: {len(results)} rows / total {total} rows")
        
        df = pd.DataFrame(results)
        
        if total > FDAConfig.MAX_ROWS:
            logger.warning(f"total {total} rows but only received {FDAConfig.MAX_ROWS} rows (pagination needed)")
        
        return df
        
    except Exception as e:
        logger.error(f"fda api failed: {e}")
        return pd.DataFrame()


def save_results(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        logger.warning("no data to save")
        return
    
    FDAConfig.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = FDAConfig.OUTPUT_DIR / filename
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logger.info(f"saved: {filepath.name} ({len(df)} rows)")


if __name__ == "__main__":
    # example
    df_drugs = fetch_compliance_actions(
        product_types=["Drugs"],
        action_types=["Warning Letter"],
        start_date="2020-01-01"
    )
    save_results(df_drugs, "fda_drugs_warnings_20241130.csv")
