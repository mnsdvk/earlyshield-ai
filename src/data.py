from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def district_catalog() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "districts.csv")

@lru_cache(maxsize=1)
def infrastructure_catalog() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "infrastructure.csv")
