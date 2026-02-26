from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DrugInfo:
    """Результат Stage 1: информация об оригинальном препарате."""
    query_inn: str
    matched_inn: str = ""
    match_type: str = ""           # "exact" | "fuzzy"
    match_score: float = 100.0
    drug_kind: str = ""            # "оригинальный" | "воспроизведённый" | ...
    trade_names: str = ""
    dosage_form: str = ""          # "таблетки, покрытые пленочной оболочкой" и т.д.
    atc_code: str = ""
    atc_name: str = ""
    holders: str = ""
    countries: str = ""
    name_latin: str = ""


@dataclass
class PKValue:
    """Одно значение ФК-параметра с указанием источника."""
    value: Optional[float] = None
    unit: str = ""
    source: str = ""               # "llm/vidal_drug" | "llm/ohlp" | "llm/edrug3d" | "edrug3d" | ...
    raw_text: str = ""             # цитата из текста
    reasoning: str = ""            # объяснение LLM почему выбрано это значение


@dataclass
class PKParams:
    """Результат Stage 2: фармакокинетические параметры."""
    cmax: Optional[PKValue] = None          # Cmax, нг/мл
    auc: Optional[PKValue] = None           # AUC, нг*ч/мл
    tmax_h: Optional[PKValue] = None        # Tmax, ч
    t_half_h: Optional[PKValue] = None      # T½, ч
    cvintra_pct: Optional[PKValue] = None   # CVintra, %

    def filled_params(self) -> dict:
        result = {}
        for name in PK_PARAM_NAMES:
            val = getattr(self, name)
            if val and val.value is not None:
                result[name] = val
        return result

    def missing_params(self) -> list:
        missing = []
        for name in PK_PARAM_NAMES:
            val = getattr(self, name)
            if not val or val.value is None:
                missing.append(name)
        return missing


PK_PARAM_NAMES = ["cmax", "auc", "tmax_h", "t_half_h", "cvintra_pct"]

PK_PARAM_LABELS = {
    "cmax": ("Cmax", "нг/мл"),
    "auc": ("AUC", "нг*ч/мл"),
    "tmax_h": ("Tmax", "ч"),
    "t_half_h": ("T½", "ч"),
    "cvintra_pct": ("CVintra", "%"),
}
