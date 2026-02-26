"""
OSP: числовые ФК параметры из клинических исследований.
Файл: data/osp_pk_parameters.csv
Колонки: Analyte, AUC Avg/Var/VarType, Cmax Avg/Var/VarType, CL Avg
"""

import csv
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import OSP_CSV, FUZZY_THRESHOLD
from ..models import PKValue

_cache = None

_CV_TYPES = {"CV", "CV%", "%CV", "arith. CV", "geo. CV", "geom. CV", "gCV"}


def _load():
    global _cache
    if _cache is None:
        with open(OSP_CSV, encoding="utf-8") as f:
            _cache = list(csv.DictReader(f))
    return _cache


def search(name_en: str) -> Optional[dict]:
    rows = _load()
    query = name_en.strip().lower()

    matched_rows = [r for r in rows if r.get("Analyte", "").strip().lower() == query]

    if not matched_rows:
        analytes = [r.get("Analyte", "").strip() for r in rows]
        matches = process.extract(query, [a.lower() for a in analytes], scorer=fuzz.WRatio, limit=5, score_cutoff=FUZZY_THRESHOLD)
        if not matches:
            return None
        best_analyte = analytes[matches[0][2]].lower()
        score = matches[0][1]
        matched_rows = [r for r in rows if r.get("Analyte", "").strip().lower() == best_analyte]
        match_type, match_score = "fuzzy", score
    else:
        match_type, match_score = "exact", 100.0

    best = max(matched_rows, key=lambda r: _count_pk_fields(r))

    cv_intra = _find_cv_intra(matched_rows)

    return _extract(best, match_type, match_score, cv_intra)


def _float_or_none(val: str) -> Optional[float]:
    try:
        v = float(val.strip())
        if v == v and v != float("inf"):
            return v
    except (ValueError, TypeError):
        pass
    return None


def _count_pk_fields(row: dict) -> int:
    return sum(1 for col in ["AUC Avg", "Cmax Avg"] if _float_or_none(row.get(col, "")) is not None)


def _find_cv_intra(matched_rows: list) -> Optional[dict]:
    """Ищет все CV% для Cmax среди строк, берёт медиану. Fallback на AUC CV."""
    import statistics

    cmax_cvs = []
    auc_cvs = []
    refs = set()

    for r in matched_rows:
        ref = r.get("Reference", "").strip()
        for prefix, acc in [("Cmax", cmax_cvs), ("AUC", auc_cvs)]:
            vtype = r.get(f"{prefix} VarType", "").strip()
            vunit = r.get(f"{prefix} VarUnit", "").strip()
            vval = _float_or_none(r.get(f"{prefix} Var", ""))
            if vtype in _CV_TYPES and vval is not None and vunit == "%":
                acc.append(vval)
                refs.add(ref)

    chosen = cmax_cvs if cmax_cvs else auc_cvs
    param = "Cmax" if cmax_cvs else "AUC"
    if not chosen:
        return None

    median_val = round(statistics.median(chosen), 1)
    refs_str = "; ".join(sorted(refs)[:3])
    return {
        "value": median_val,
        "param": param,
        "n_studies": len(chosen),
        "all_values": chosen,
        "reference": refs_str,
    }


def _convert_auc(value: float, unit: str) -> tuple:
    u = unit.strip().lower()
    if "µg" in u or "ug" in u or "mcg" in u:
        if "h" in u and "ml" in u:
            return value * 1000, "нг*ч/мл"
    if "ng" in u and "h" in u and "ml" in u:
        return value, "нг*ч/мл"
    if "mg" in u and "h" in u and "ml" in u:
        return value * 1_000_000, "нг*ч/мл"
    return value, unit


def _convert_cmax(value: float, unit: str) -> tuple:
    u = unit.strip().lower()
    if "µg" in u or "ug" in u or "mcg" in u:
        if "ml" in u:
            return value * 1000, "нг/мл"
    if "ng" in u and "ml" in u:
        return value, "нг/мл"
    if "mg" in u and "ml" in u:
        return value * 1_000_000, "нг/мл"
    return value, unit


def _extract(row: dict, match_type: str, score: float, cv_intra: Optional[dict]) -> dict:
    result = {
        "source": "osp",
        "matched_name": row.get("Analyte", "").strip(),
        "study": row.get("Reference", "").strip(),
        "match_type": match_type,
        "match_score": score,
        "params": {},
    }

    val = _float_or_none(row.get("AUC Avg", ""))
    if val is not None:
        raw_unit = row.get("AUC AvgUnit", "").strip()
        conv_val, conv_unit = _convert_auc(val, raw_unit)
        result["params"]["auc"] = PKValue(
            value=conv_val, unit=conv_unit, source="osp",
            raw_text=f"{val} {raw_unit}",
        )

    val = _float_or_none(row.get("Cmax Avg", ""))
    if val is not None:
        raw_unit = row.get("Cmax AvgUnit", "").strip()
        conv_val, conv_unit = _convert_cmax(val, raw_unit)
        result["params"]["cmax"] = PKValue(
            value=conv_val, unit=conv_unit, source="osp",
            raw_text=f"{val} {raw_unit}",
        )

    if cv_intra:
        vals_str = ", ".join(f"{v}%" for v in cv_intra["all_values"])
        result["params"]["cvintra_pct"] = PKValue(
            value=cv_intra["value"],
            unit="%",
            source="osp",
            raw_text=(
                f"{cv_intra['param']} CV median={cv_intra['value']}% "
                f"(n={cv_intra['n_studies']}: {vals_str}) | {cv_intra['reference']}"
            ),
        )

    return result
