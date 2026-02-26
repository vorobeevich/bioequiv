"""
Стадия 1: МНН + форма → оригинальный препарат.

Источник: data/eaeu_registry.csv
Метод: exact match → fuzzy (rapidfuzz) → LLM-валидация fuzzy-матчей
       + опциональная фильтрация по лекарственной форме
"""

import csv
from typing import List, Optional

from rapidfuzz import fuzz, process

from .config import EAEU_REGISTRY_CSV, FUZZY_THRESHOLD, DEEPSEEK_API_KEY
from .models import DrugInfo


def _load_registry() -> list:
    with open(EAEU_REGISTRY_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


_registry_cache = None


def _get_registry() -> list:
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = _load_registry()
    return _registry_cache


def _llm_validate_inn(query: str, matched: str) -> bool:
    """LLM проверяет: matched — это то же вещество, что и query?"""
    if not DEEPSEEK_API_KEY:
        return True
    try:
        from .stage2_sources.llm_extract import validate_fuzzy_match
        vr = validate_fuzzy_match(query, matched)
        return vr.is_same
    except Exception:
        return True


def _normalize_form(form: str) -> str:
    """Нормализует строку формы для сравнения."""
    return form.strip().lower().replace(",", "").replace(".", "")


_FORM_KEYWORDS = {
    "таблетки": ["таблетк", "табл"],
    "капсулы": ["капсул"],
    "раствор": ["раствор"],
    "суспензия": ["суспензи"],
    "мазь": ["мазь"],
    "гель": ["гель"],
    "крем": ["крем"],
    "капли": ["капл"],
    "сироп": ["сироп"],
    "порошок": ["порошок", "порошк"],
    "суппозитории": ["суппозитори", "свечи"],
    "спрей": ["спрей"],
    "аэрозоль": ["аэрозоль"],
    "инъекции": ["инъекц", "для внутривенн", "для внутримышечн", "для подкожн"],
    "инфузии": ["инфузи"],
}


def _form_matches(query_form: str, registry_form: str) -> bool:
    """Проверяет, подходит ли форма из реестра под запрос пользователя."""
    if not query_form:
        return True
    if not registry_form:
        return False

    q = _normalize_form(query_form)
    r = _normalize_form(registry_form)

    if q in r or r in q:
        return True

    for canonical, keywords in _FORM_KEYWORDS.items():
        q_match = any(kw in q for kw in keywords) or canonical in q
        r_match = any(kw in r for kw in keywords) or canonical in r
        if q_match and r_match:
            return True

    return False


def _filter_by_form(results: List[DrugInfo], query_form: str) -> List[DrugInfo]:
    """Фильтрует результаты по форме, если указана. Если после фильтрации пусто — вернёт все."""
    if not query_form:
        return results
    filtered = [d for d in results if _form_matches(query_form, d.dosage_form)]
    return filtered if filtered else results


def search_by_inn(query_inn: str, query_form: str = "",
                  use_llm: bool = True) -> List[DrugInfo]:
    """
    Ищет все записи реестра по МНН.
    Опционально фильтрует по лекарственной форме.
    Возвращает список DrugInfo (все типы: оригинальный, воспроизведённый, ...).
    """
    registry = _get_registry()
    query_lower = query_inn.strip().lower()

    results = []

    for row in registry:
        if row["inn"].strip().lower() == query_lower:
            results.append(_row_to_drug_info(row, query_inn, "exact", 100.0))

    if results:
        return _filter_by_form(results, query_form)

    inn_values = [row["inn"].strip() for row in registry]
    matches = process.extract(
        query_lower,
        [v.lower() for v in inn_values],
        scorer=fuzz.WRatio,
        limit=10,
        score_cutoff=FUZZY_THRESHOLD,
    )

    matched_inns = set()
    for match_text, score, idx in matches:
        original_inn = inn_values[idx]
        if original_inn.lower() in matched_inns:
            continue
        matched_inns.add(original_inn.lower())

        if use_llm:
            if not _llm_validate_inn(query_inn, original_inn):
                continue

        for row in registry:
            if row["inn"].strip().lower() == original_inn.lower():
                results.append(_row_to_drug_info(row, query_inn, "fuzzy", score))

    return _filter_by_form(results, query_form)


def find_original(query_inn: str, query_form: str = "",
                  use_llm: bool = True) -> Optional[DrugInfo]:
    """
    Основная функция Stage 1.
    Ищет оригинальный препарат по МНН (и опционально форме).
    Возвращает DrugInfo или None.
    """
    all_matches = search_by_inn(query_inn, query_form=query_form, use_llm=use_llm)
    if not all_matches:
        return None

    originals = [d for d in all_matches if d.drug_kind == "оригинальный"]
    if originals:
        return originals[0]

    return all_matches[0]


def find_all_by_inn(query_inn: str, query_form: str = "",
                    use_llm: bool = True) -> List[DrugInfo]:
    """Возвращает все записи (оригинальные + дженерики) для отображения пользователю."""
    return search_by_inn(query_inn, query_form=query_form, use_llm=use_llm)


def get_unique_forms(query_inn: str = "") -> List[str]:
    """Возвращает список уникальных лекарственных форм (опционально для конкретного МНН)."""
    registry = _get_registry()
    forms = set()
    for row in registry:
        form = row.get("dosage_form", "").strip()
        if not form:
            continue
        if query_inn:
            if row["inn"].strip().lower() != query_inn.strip().lower():
                continue
        forms.add(form)
    return sorted(forms)


def _row_to_drug_info(row: dict, query_inn: str, match_type: str, score: float) -> DrugInfo:
    return DrugInfo(
        query_inn=query_inn,
        matched_inn=row["inn"].strip(),
        match_type=match_type,
        match_score=score,
        drug_kind=row.get("drug_kind", "").strip(),
        trade_names=row.get("trade_names", "").strip(),
        dosage_form=row.get("dosage_form", "").strip(),
        atc_code=row.get("atc_code", "").strip(),
        atc_name=row.get("atc_name", "").strip(),
        holders=row.get("holders", "").strip(),
        countries=row.get("countries", "").strip(),
    )
