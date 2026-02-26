"""
FDA Product-Specific Guidances (PSG) — рекомендации по дизайну БЭ-исследований.
Файл: data/fda_psg_parsed.csv

Назначение:
  - Собираем и показываем пользователю данные по дизайну исследования (Стадия 3)
  - В промпт LLM отправляем ТОЛЬКО: CVintra-порог и флаг реплицированного дизайна

Поиск:
  1. По имени вещества (English, exact → fuzzy)
  2. Если нашли fuzzy — возвращаем сырой результат (LLM-валидация снаружи)

Возвращает dict:
  source            "fda_psg"
  substance         вещество из FDA
  form_route        лекформа / путь введения
  dosage_form
  num_studies
  design_fasting
  design_fed
  strength
  subjects
  analytes
  be_based_on
  waiver
  additional_comments
  is_replicated     bool
  is_hvd            bool — mentions high variability
  cvintra_threshold int|None — порог CVintra, если явно указан (обычно 30 %)
  is_nti            bool
  dissolution_info
  pdf_url           прямая ссылка на FDA PDF
  local_pdf         относительный путь (для offline-доступа)
  match_type        "exact" | "fuzzy"
  match_score       float (0–100)
"""

import csv
import re
from typing import Optional

from rapidfuzz import fuzz, process

from ..config import FDA_PSG_CSV, FDA_PSG_ENABLED, FUZZY_THRESHOLD

_cache: Optional[list] = None

_BOOL_TRUE = {"True", "true", "1", "yes"}


def _load():
    global _cache
    if _cache is None:
        if not FDA_PSG_ENABLED:
            _cache = []
            return _cache
        with open(FDA_PSG_CSV, encoding="utf-8") as f:
            _cache = list(csv.DictReader(f))
    return _cache


def _to_bool(val: str) -> bool:
    return val.strip() in _BOOL_TRUE


def _to_int(val: str) -> Optional[int]:
    try:
        return int(val.strip())
    except (ValueError, TypeError):
        return None


def _norm(name: str) -> str:
    """Нормализация: строчные, убираем соли/форму/лишнее."""
    name = name.lower()
    # убираем соли и скобки
    name = re.sub(r"\s+(hydrochloride|hcl|sodium|calcium|besylate|mesylate|"
                  r"hemifumarate|sulfate|maleate|tartrate|acetate|phosphate|"
                  r"fumarate|citrate|succinate|bitartrate|bromide|chloride)\b", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)
    name = re.sub(r"[;,:].*", "", name)  # отбрасываем второй компонент комбо
    return name.strip()


def _build_index(rows: list) -> tuple[list, list]:
    """Возвращает (names_norm, names_raw) для rapidfuzz."""
    names_norm = [_norm(r.get("substance", "")) for r in rows]
    names_raw = [r.get("substance", "") for r in rows]
    return names_norm, names_raw


def _make_result(row: dict, match_type: str, score: float) -> dict:
    cvintra_raw = row.get("cvintra_threshold", "")
    cv_val = _to_int(cvintra_raw) if cvintra_raw else None

    return {
        "source": "fda_psg",
        "substance": row.get("substance", "").strip(),
        "form_route": row.get("form_route", "").strip(),
        "dosage_form": row.get("dosage_form", "").strip(),
        "num_studies": _to_int(row.get("num_studies", "")) or 0,
        "design_fasting": row.get("design_fasting", "").strip(),
        "design_fed": row.get("design_fed", "").strip(),
        "strength": row.get("strength", "").strip(),
        "subjects": row.get("subjects", "").strip(),
        "analytes": row.get("analytes", "").strip(),
        "be_based_on": row.get("be_based_on", "").strip(),
        "waiver": row.get("waiver", "").strip(),
        "additional_comments": row.get("additional_comments", "").strip(),
        "is_replicated": _to_bool(row.get("is_replicated", "")),
        "is_hvd": _to_bool(row.get("is_hvd", "")),
        "cvintra_threshold": cv_val,
        "is_nti": _to_bool(row.get("is_nti", "")),
        "dissolution_info": row.get("dissolution_info", "").strip(),
        "pdf_url": row.get("pdf_url", "").strip(),
        "local_pdf": row.get("local_pdf", "").strip(),
        "match_type": match_type,
        "match_score": score,
    }


def search(name_en: str, dosage_form: str = "") -> Optional[dict]:
    """
    Ищет FDA PSG по английскому названию вещества.
    dosage_form (необязательно) — фильтрует результаты по форме (tablet, capsule, …).
    Возвращает наиболее релевантный результат или None.
    """
    rows = _load()
    if not rows:
        return None

    query_norm = _norm(name_en)
    names_norm, _ = _build_index(rows)

    # ── 1. Exact ───────────────────────────────────────────────────────────
    exact_idxs = [i for i, n in enumerate(names_norm) if n == query_norm]
    if exact_idxs:
        candidates = [rows[i] for i in exact_idxs]
        best = _pick_best(candidates, dosage_form)
        return _make_result(best, "exact", 100.0)

    # ── 2. Fuzzy ───────────────────────────────────────────────────────────
    matches = process.extract(
        query_norm, names_norm,
        scorer=fuzz.WRatio, limit=5, score_cutoff=FUZZY_THRESHOLD
    )
    if not matches:
        return None

    best_score = matches[0][1]
    top_score_idxs = [m[2] for m in matches if m[1] >= best_score - 5]
    candidates = [rows[i] for i in top_score_idxs]
    best = _pick_best(candidates, dosage_form)
    return _make_result(best, "fuzzy", best_score)


def _pick_best(candidates: list, dosage_form: str) -> dict:
    """Из кандидатов выбирает наиболее подходящий: сначала по лекформе, потом самый информативный."""
    if dosage_form:
        df_low = dosage_form.lower()
        filtered = [c for c in candidates
                    if df_low in c.get("dosage_form", "").lower()
                    or df_low in c.get("form_route", "").lower()]
        if filtered:
            candidates = filtered

    def _score(r):
        return (
            int(_to_bool(r.get("is_hvd", ""))) * 10 +
            int(_to_bool(r.get("is_replicated", ""))) * 5 +
            int(bool(r.get("design_fasting", "").strip())) * 3 +
            int(bool(r.get("additional_comments", "").strip())) * 2 +
            int(bool(r.get("pdf_url", "").strip()))
        )

    return max(candidates, key=_score)


def search_all(name_en: str) -> list:
    """Возвращает ВСЕ записи для данного вещества (разные дозировки/формы)."""
    rows = _load()
    if not rows:
        return []

    query_norm = _norm(name_en)
    names_norm, _ = _build_index(rows)

    exact_idxs = [i for i, n in enumerate(names_norm) if n == query_norm]
    if exact_idxs:
        return [_make_result(rows[i], "exact", 100.0) for i in exact_idxs]

    matches = process.extract(
        query_norm, names_norm,
        scorer=fuzz.WRatio, limit=10, score_cutoff=FUZZY_THRESHOLD
    )
    if not matches:
        return []

    best_score = matches[0][1]
    results = []
    for _, score, idx in matches:
        if score >= best_score - 5:
            results.append(_make_result(rows[idx], "fuzzy", score))
    return results
