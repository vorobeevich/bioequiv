"""
CVintra из публикации PMC6989220 (Park et al. 2020).
Данные: pooled intra-subject CV из 142 BE-исследований Кореи (MFDS).
53 уникальных вещества. Включает CVintra Cmax, AUC, рекомендуемый размер выборки.
Файл: data/cvintra_pmc.csv
"""

import csv
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import CVINTRA_PMC_CSV, FUZZY_THRESHOLD
from ..models import PKValue

_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            with open(CVINTRA_PMC_CSV, encoding="utf-8") as f:
                _cache = list(csv.DictReader(f))
        except FileNotFoundError:
            _cache = []
    return _cache


def search(name_en: str) -> Optional[dict]:
    rows = _load()
    if not rows:
        return None

    query = name_en.strip().lower()
    names = [r["active_ingredient"].strip() for r in rows]

    exact = [i for i, n in enumerate(names) if n.lower() == query]
    if exact:
        return _result(rows[exact[0]], "exact", 100.0)

    matches = process.extract(
        query, [n.lower() for n in names],
        scorer=fuzz.WRatio, limit=3, score_cutoff=FUZZY_THRESHOLD,
    )
    if matches:
        return _result(rows[matches[0][2]], "fuzzy", matches[0][1])

    return None


def _fval(v):
    try:
        f = float(v)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def _result(row: dict, match_type: str, score: float) -> dict:
    cv_cmax = _fval(row.get("cvintra_cmax_pct"))
    cv_auc = _fval(row.get("cvintra_auc_pct"))
    n = row.get("n_studies", "")
    ss80 = row.get("sample_size_80pwr", "")
    ss90 = row.get("sample_size_90pwr", "")

    r = {
        "source": "cvintra_pmc",
        "matched_name": row["active_ingredient"],
        "match_type": match_type,
        "match_score": score,
        "n_studies": n,
        "sample_size_80pwr": ss80,
        "sample_size_90pwr": ss90,
        "cvintra_cmax_pct": cv_cmax,
        "cvintra_auc_pct": cv_auc,
        "reference": "Park et al. Transl Clin Pharmacol. 2020;28(1):52-62",
        "reference_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6989220/",
        "params": {},
    }

    cv_val = cv_cmax or cv_auc
    if cv_val:
        parts = []
        if cv_cmax:
            parts.append(f"Cmax CV={cv_cmax}%")
        if cv_auc:
            parts.append(f"AUC CV={cv_auc}%")
        if n:
            parts.append(f"n={n} BE studies")
        if ss80:
            parts.append(f"sample size: {ss80} (80% pwr) / {ss90} (90% pwr)")

        r["params"]["cvintra_pct"] = PKValue(
            value=cv_val, unit="%", source="cvintra_pmc",
            raw_text=" | ".join(parts),
        )

    return r
