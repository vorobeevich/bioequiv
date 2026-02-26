"""
DrugBank: текстовые ФК описания.
Файл: data/drugbank_pk.csv
"""

import csv
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import DRUGBANK_CSV, FUZZY_THRESHOLD

csv.field_size_limit(10_000_000)

_cache = None


def _load():
    global _cache
    if _cache is None:
        with open(DRUGBANK_CSV, encoding="utf-8", errors="replace") as f:
            _cache = list(csv.DictReader(f))
    return _cache


def search(name_en: str) -> Optional[dict]:
    rows = _load()
    query = name_en.strip().lower()

    for row in rows:
        if row.get("inn", "").strip().lower() == query:
            return _result(row, "exact_inn", 100.0)

    for row in rows:
        if row.get("name", "").strip().lower() == query:
            return _result(row, "exact_name", 100.0)

    names = [row.get("name", "").strip() for row in rows]
    matches = process.extract(query, [n.lower() for n in names], scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD)
    if matches:
        _, score, idx = matches[0]
        return _result(rows[idx], "fuzzy", score)

    return None


def _result(row: dict, match_type: str, score: float) -> dict:
    db_id = row.get("drugbank_id", "").strip()
    url = f"https://go.drugbank.com/drugs/{db_id}" if db_id else ""
    return {
        "source": "drugbank",
        "drugbank_id": db_id,
        "url": url,
        "matched_name": row.get("name", "").strip(),
        "match_type": match_type,
        "match_score": score,
        "half_life": row.get("half_life", "").strip(),
        "protein_binding": row.get("protein_binding", "").strip(),
        "volume_of_distribution": row.get("volume_of_distribution", "").strip(),
        "clearance": row.get("clearance", "").strip(),
        "absorption": row.get("absorption", "").strip(),
        "metabolism": row.get("metabolism", "").strip(),
        "route_of_elimination": row.get("route_of_elimination", "").strip(),
    }
