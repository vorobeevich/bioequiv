"""
Видаль: два уровня поиска.

1. Препараты (vidal_drugs_merged.csv) — 10 500+ записей
   → торговое название → ФК, фармакология, показания, противопоказания, побочные

2. Молекулы / активные вещества (vidal_molecules.csv) — 4 600+ записей
   → мост рус↔лат, фармакокинетика, URL

Приоритет: препарат > вещество.
"""

import csv
import re
from typing import Optional, List

from rapidfuzz import fuzz, process

from ..config import (
    VIDAL_MOLECULES_CSV,
    VIDAL_DRUGS_CSV,
    FUZZY_THRESHOLD,
)

csv.field_size_limit(10_000_000)

_mol_cache = None
_drug_cache = None


def _load_molecules():
    global _mol_cache
    if _mol_cache is None:
        with open(VIDAL_MOLECULES_CSV, encoding="utf-8", errors="replace") as f:
            _mol_cache = list(csv.DictReader(f))
    return _mol_cache


def _load_drugs():
    global _drug_cache
    if _drug_cache is None:
        import os
        if not os.path.exists(VIDAL_DRUGS_CSV):
            _drug_cache = []
            return _drug_cache
        with open(VIDAL_DRUGS_CSV, encoding="utf-8", errors="replace") as f:
            _drug_cache = list(csv.DictReader(f))
    return _drug_cache


def _clean_name(s: str) -> str:
    return re.sub(r'[®™\s()\-]+', ' ', s).strip().lower()


def search_molecule(query: str) -> Optional[dict]:
    """Поиск активного вещества по русскому или латинскому названию."""
    rows = _load_molecules()
    q = query.strip().lower()

    for row in rows:
        if row["name_ru"].strip().lower() == q:
            return _mol_result(row, "exact", 100.0)

    for row in rows:
        if row.get("name_latin", "").strip().lower() == q:
            return _mol_result(row, "exact_latin", 100.0)

    names_ru = [row["name_ru"].strip() for row in rows]
    matches = process.extract(q, [n.lower() for n in names_ru], scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD)
    if matches:
        _, score, idx = matches[0]
        return _mol_result(rows[idx], "fuzzy", score)

    names_lat = [row.get("name_latin", "").strip() for row in rows]
    matches = process.extract(q, [n.lower() for n in names_lat], scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD)
    if matches:
        _, score, idx = matches[0]
        return _mol_result(rows[idx], "fuzzy_latin", score)

    return None


def search_drug(trade_name: str) -> Optional[dict]:
    """Поиск препарата по торговому названию в единой таблице."""
    q = trade_name.strip().lower()
    q_clean = _clean_name(trade_name)

    rows = _load_drugs()
    if not rows:
        return None

    for row in rows:
        rn = row.get("name", "").strip().lower()
        if rn == q or _clean_name(row.get("name", "")) == q_clean:
            return _drug_result(row, "exact", 100.0)

    names_clean = [_clean_name(row.get("name", "")) for row in rows]
    matches = process.extract(q_clean, names_clean, scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD)
    if matches:
        _, score, idx = matches[0]
        return _drug_result(rows[idx], "fuzzy", score)

    return None


def search_drugs_by_molecule(molecule_ru: str) -> List[dict]:
    """Найти все препараты, содержащие данную молекулу."""
    q = molecule_ru.strip().lower()
    results = []
    for row in _load_drugs():
        if row.get("molecule_name", "").strip().lower() == q:
            results.append({
                "drug_name": row.get("name", "").strip(),
                "owner": row.get("owner", "").strip(),
                "has_pk": bool(row.get("pharmacokinetics", "").strip()),
            })
    return results


# Backward compat
def search(query: str) -> Optional[dict]:
    return search_molecule(query)


def _mol_result(row: dict, match_type: str, score: float) -> dict:
    url = row.get("url", "").strip()
    return {
        "source": "vidal",
        "level": "molecule",
        "name_ru": row.get("name_ru", "").strip(),
        "name_latin": row.get("name_latin", "").strip(),
        "url": url,
        "pharmacokinetics": row.get("pharmacokinetics", "").strip(),
        "pharmacology": row.get("pharmacology", "").strip(),
        "indications": row.get("indications", "").strip(),
        "contraindications": row.get("contraindications", "").strip(),
        "drugs_count": int(row.get("drugs_count", 0) or 0),
        "match_type": match_type,
        "match_score": score,
    }


def _drug_result(row: dict, match_type: str, score: float) -> dict:
    """Результат из единой таблицы препаратов."""
    mol_name = row.get("molecule_name", "").strip()
    mol = search_molecule(mol_name) if mol_name else None
    name_latin = mol.get("name_latin", "") if mol else ""

    return {
        "source": "vidal",
        "level": "drug",
        "drug_name": row.get("name", "").strip(),
        "drug_url": row.get("url", "").strip(),
        "owner": row.get("owner", "").strip(),
        "molecule_ru": mol_name,
        "molecule_url": row.get("molecule_url", "").strip(),
        "name_latin": name_latin,
        "pharmacokinetics": row.get("pharmacokinetics", "").strip(),
        "pharmacology": row.get("pharmacology", "").strip(),
        "form_details": row.get("form_details", "").strip(),
        "match_type": match_type,
        "match_score": score,
    }
