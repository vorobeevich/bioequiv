"""
e-Drug3D: числовые ФК параметры.
Файл: data/edrug3d_pk.csv
Колонки: name, tmax_h, t_half_h, cmax, cmax_unit
"""

import csv
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import EDRUG3D_CSV, FUZZY_THRESHOLD
from ..models import PKValue

_cache = None


def _load():
    global _cache
    if _cache is None:
        with open(EDRUG3D_CSV, encoding="utf-8") as f:
            _cache = list(csv.DictReader(f))
    return _cache


def search(name_en: str) -> Optional[dict]:
    rows = _load()
    query = name_en.strip().lower()

    for row in rows:
        if row["name"].strip().lower() == query:
            return _extract(row, "exact", 100.0)

    names = [row["name"].strip() for row in rows]
    matches = process.extract(query, [n.lower() for n in names], scorer=fuzz.WRatio, limit=1, score_cutoff=FUZZY_THRESHOLD)
    if matches:
        _, score, idx = matches[0]
        return _extract(rows[idx], "fuzzy", score)

    return None


def _float_or_none(val: str) -> Optional[float]:
    try:
        v = float(val.strip())
        if v == v and v != float("inf"):
            return v
    except (ValueError, TypeError):
        pass
    return None


def _convert_cmax_to_ng_ml(value: float, unit: str, name: str) -> Optional[tuple]:
    """Конвертирует Cmax в нг/мл. Возвращает (value, unit) или None."""
    unit_upper = unit.strip().upper()

    if unit_upper in ("NG/ML", "NANOGRAM/ML"):
        return value, "нг/мл"
    elif unit_upper in ("UG/ML", "MICROGRAM/ML", "MCG/ML"):
        return value * 1000, "нг/мл"
    elif unit_upper in ("MG/ML",):
        return value * 1_000_000, "нг/мл"
    elif unit_upper in ("PG/ML",):
        return value / 1000, "нг/мл"
    elif unit_upper in ("NANOMOLAR", "NM", "MICROMOLAR", "UM"):
        return None
    else:
        return value, unit


def _extract(row: dict, match_type: str, score: float) -> dict:
    result = {
        "source": "edrug3d",
        "matched_name": row["name"].strip(),
        "match_type": match_type,
        "match_score": score,
        "params": {},
    }

    # Tmax
    val = _float_or_none(row.get("tmax_h", ""))
    if val is not None:
        result["params"]["tmax_h"] = PKValue(value=val, unit="ч", source="edrug3d")

    # T½
    val = _float_or_none(row.get("t_half_h", ""))
    if val is not None:
        result["params"]["t_half_h"] = PKValue(value=val, unit="ч", source="edrug3d")

    # Cmax (с конвертацией единиц)
    val = _float_or_none(row.get("cmax", ""))
    if val is not None:
        raw_unit = row.get("cmax_unit", "").strip()
        converted = _convert_cmax_to_ng_ml(val, raw_unit, row["name"].strip())
        if converted:
            result["params"]["cmax"] = PKValue(
                value=converted[0], unit=converted[1], source="edrug3d",
                raw_text=f"{val} {raw_unit}",
            )
        else:
            result["cmax_molar"] = f"{val} {raw_unit}"

    return result
