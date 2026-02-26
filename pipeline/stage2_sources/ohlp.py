"""
ЕАЭС ОХЛП: все извлечённые разделы из PDF ОХЛП.

data/ohlp_pk_texts.csv — 15 разделов:
  composition_text (2), form_text (3),
  indications_text (4.1), dosing_text (4.2), contra_text (4.3),
  precautions_text (4.4), interactions_text (4.5), pregnancy_text (4.6),
  adverse_text (4.8), overdose_text (4.9),
  pd_text (5.1), pk_text (5.2),
  excipients_text (6.1), shelf_life_text (6.3), storage_text (6.4)
"""

import csv
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import OHLP_CSV, OHLP_ENABLED, FUZZY_THRESHOLD

csv.field_size_limit(10_000_000)

_cache = None


def _load():
    global _cache
    if _cache is None:
        if not OHLP_ENABLED:
            _cache = []
            return _cache
        with open(OHLP_CSV, encoding="utf-8", errors="replace") as f:
            _cache = list(csv.DictReader(f))
    return _cache


def search(inn_ru: str, trade_name: str = "") -> Optional[dict]:
    """
    Двухуровневый поиск в ОХЛП:
      1) По ПРЕПАРАТУ (trade_name): exact → fuzzy → LLM-валидация
      2) По ВЕЩЕСТВУ (inn): exact → fuzzy → LLM-валидация

    level в результате: "drug" (по препарату) или "substance" (по МНН).
    """
    if not OHLP_ENABLED:
        return None

    rows = _load()
    if not rows:
        return None

    # ── 1. Поиск по ПРЕПАРАТУ (trade_name) ──
    if trade_name:
        q_trade = trade_name.strip().lower()

        for row in rows:
            if row.get("trade_name", "").strip().lower() == q_trade:
                if _has_useful_text(row):
                    return _result(row, "exact_trade", 100.0, level="drug")

        trade_names = [row.get("trade_name", "").strip() for row in rows]
        matches = process.extract(
            q_trade, [n.lower() for n in trade_names],
            scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD,
        )
        if matches:
            _, score, idx = matches[0]
            if _has_useful_text(rows[idx]):
                return _result(rows[idx], "fuzzy_trade", score, level="drug")

    # ── 2. Поиск по ВЕЩЕСТВУ (МНН) ──
    q_inn = inn_ru.strip().lower()

    for row in rows:
        if row.get("inn", "").strip().lower() == q_inn:
            if _has_useful_text(row):
                return _result(row, "exact", 100.0, level="substance")

    inns = [row.get("inn", "").strip() for row in rows]
    matches = process.extract(
        q_inn, [n.lower() for n in inns],
        scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD,
    )
    if matches:
        _, score, idx = matches[0]
        if _has_useful_text(rows[idx]):
            return _result(rows[idx], "fuzzy", score, level="substance")

    return None


_TEXT_FIELDS = (
    "composition_text", "form_text",
    "indications_text", "dosing_text", "contra_text",
    "precautions_text", "interactions_text", "pregnancy_text",
    "adverse_text", "overdose_text",
    "pd_text", "pk_text",
    "excipients_text", "shelf_life_text", "storage_text",
)


def _has_useful_text(row: dict) -> bool:
    return any(len(row.get(f, "").strip()) > 30 for f in _TEXT_FIELDS)


def _result(row: dict, match_type: str, score: float, level: str = "substance") -> dict:
    r = {
        "source": "ohlp",
        "level": level,  # "drug" | "substance"
        "matched_inn": row.get("inn", "").strip(),
        "matched_trade_name": row.get("trade_name", "").strip(),
        "match_type": match_type,
        "match_score": score,
    }
    for f in _TEXT_FIELDS:
        r[f] = row.get(f, "").strip()
    return r
