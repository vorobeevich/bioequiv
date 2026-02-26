"""
DeepSeek LLM:
1) Извлечение числовых ФК параметров из текстовых описаний.
2) Валидация fuzzy-матчей (parabomol vs paracetamol).
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
from ..models import PKValue

EXTRACTION_PROMPT = """Ты фармаколог-эксперт. Тебе даны ВСЕ собранные данные для одного лекарства из разных источников.

Источники помечены тегами:
  [ПРЕПАРАТ/vidal_drug] — текст фармакокинетики со страницы конкретного торгового препарата на Видале
  [ПРЕПАРАТ/ohlp] — текст из ОХЛП конкретного препарата (найден по торговому названию)
  [ВЕЩЕСТВО/ohlp] — текст из ОХЛП другого препарата с тем же МНН (найден по веществу)
  [ВЕЩЕСТВО/edrug3d] — готовые числа из базы e-Drug3D (для активного вещества)
  [ВЕЩЕСТВО/osp] — готовые числа из базы OSP (для активного вещества)
  [ВЕЩЕСТВО/cvintra_pmc] — CVintra из 142 BE-исследований (Park et al. 2020, PMC6989220), самый надёжный источник CVintra
  [ВЕЩЕСТВО/drugbank] — текст из DrugBank (для активного вещества, на английском)
  [ВЕЩЕСТВО/vidal_mol] — текст фармакокинетики со страницы вещества на Видале

ПРИОРИТЕТ (от лучшего к худшему):
  1. [ПРЕПАРАТ] — данные именно для конкретного препарата, самые точные и релевантные
  2. [ВЕЩЕСТВО] готовые числа (edrug3d, osp) — проверенные, но для вещества в целом
  3. [ВЕЩЕСТВО] текст (drugbank, vidal_mol) — полезно, но наименее специфично

Если параметр есть и в [ПРЕПАРАТ], и в [ВЕЩЕСТВО] — ВСЕГДА бери из [ПРЕПАРАТ].
Если в [ПРЕПАРАТ] нет — бери из [ВЕЩЕСТВО], предпочитая готовые числа тексту.

Твоя задача: для КАЖДОГО из 5 параметров выбрать лучшее значение.

Верни строго JSON (без markdown, без ```):
{
  "cmax": {"value": <число или null>, "unit": "нг/мл", "source_tag": "<тег>", "source_text": "<цитата>", "reasoning": "<почему>"},
  "auc": {"value": <число или null>, "unit": "нг*ч/мл", "source_tag": "...", "source_text": "...", "reasoning": "..."},
  "tmax_h": {"value": <число или null>, "unit": "ч", "source_tag": "...", "source_text": "...", "reasoning": "..."},
  "t_half_h": {"value": <число или null>, "unit": "ч", "source_tag": "...", "source_text": "...", "reasoning": "..."},
  "cvintra_pct": {"value": <число или null>, "unit": "%", "source_tag": "...", "source_text": "...", "reasoning": "..."}
}

Поля:
- source_tag: id источника (напр. "vidal_drug", "ohlp", "edrug3d", "osp", "drugbank", "vidal_mol")
- source_text: точная цитата (1-2 предложения) откуда взято число
- reasoning: 1 предложение на русском — почему выбран именно этот источник и значение
- Если value = null — все остальные поля тоже null

Правила извлечения:
- Только ЯВНО указанные числа. Не придумывай
- Диапазон "2-4 ч" → среднее: 3
- Приведи к единицам: Cmax→нг/мл, AUC→нг*ч/мл, Tmax/T½→ч, CVintra→%
- Пересчёты: мкг/мл×1000→нг/мл, мин÷60→ч, µM×MW→нг/мл

ОСОБО ПРО CVintra:
CVintra — внутрисубъектный коэффициент вариации (intra-subject / within-subject / intraindividual CV).
Синонимы в текстах (русских и английских):
  «коэффициент вариации», «вариабельность», «CV%», «% CV», «coefficient of variation»,
  «intra-subject variability», «within-subject CV», «intraindividual variability»,
  «geo. CV», «geometric CV», «CV for Cmax», «CV for AUC».
Если есть CV отдельно для Cmax и для AUC — бери CV для Cmax (обычно выше, определяет размер выборки).
Если указано SD вместо CV — не пересчитывай, напиши null (SD ≠ CV без среднего).
- Если параметра нет ни в одном источнике — null"""

VALIDATION_PROMPT = """Ты фармаколог. Определи: является ли "{matched}" тем же лекарственным веществом, что и "{query}"?
Учитывай синонимы, МНН, торговые названия.
Ответь строго JSON: {{"same": true}} или {{"same": false, "reason": "кратко почему"}}"""


@dataclass
class LLMExtractionResult:
    params: Dict[str, PKValue] = field(default_factory=dict)
    system_prompt: str = ""
    user_prompt: str = ""
    raw_response: str = ""
    error: Optional[str] = None
    model: str = ""


@dataclass
class LLMValidationResult:
    is_same: bool = False
    reason: str = ""
    raw_response: str = ""
    error: Optional[str] = None


def _get_client():
    if not DEEPSEEK_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(base_url="https://api.deepseek.com", api_key=DEEPSEEK_API_KEY)
    except ImportError:
        return None


def validate_fuzzy_match(query: str, matched: str) -> LLMValidationResult:
    """Через LLM проверяет: matched — это то же вещество, что и query?"""
    result = LLMValidationResult()
    client = _get_client()
    if not client:
        result.is_same = True
        result.reason = "LLM недоступна, пропускаем валидацию"
        return result

    prompt = VALIDATION_PROMPT.format(query=query, matched=matched)
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        result.raw_response = raw
        data = json.loads(raw)
        result.is_same = bool(data.get("same", False))
        result.reason = data.get("reason", "")
    except Exception as e:
        result.error = str(e)
        result.is_same = True
    return result


def extract_pk_from_texts(texts: Dict[str, str], missing_params: list, extra_context: str = "") -> LLMExtractionResult:
    result = LLMExtractionResult(model=DEEPSEEK_MODEL)

    if not DEEPSEEK_API_KEY or not texts or not missing_params:
        result.error = "API ключ не задан" if not DEEPSEEK_API_KEY else "Нет текстов или параметров"
        return result

    client = _get_client()
    if not client:
        result.error = "openai не установлен (pip install openai)"
        return result

    combined_text = ""
    sources_used = []
    for source, text in texts.items():
        if text and text.strip():
            combined_text += f"\n\n=== Источник: {source} ===\n{text.strip()}"
            sources_used.append(source)

    if not combined_text.strip():
        result.error = "Тексты пусты"
        return result

    result.system_prompt = EXTRACTION_PROMPT
    user_msg = f"Нужно извлечь: {', '.join(missing_params)}\n\nТексты:{combined_text}"
    if extra_context:
        user_msg += extra_context
    result.user_prompt = user_msg

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        result.raw_response = raw
        data = json.loads(raw)
    except Exception as e:
        result.error = str(e)
        return result

    for param in missing_params:
        val_info = data.get(param)
        if val_info and isinstance(val_info, dict) and val_info.get("value") is not None:
            try:
                fval = float(val_info["value"])
                source_tag = val_info.get("source_tag", "")
                source_text = val_info.get("source_text", "")
                reasoning = val_info.get("reasoning", "")
                if source_tag:
                    source_name = f"llm/{source_tag}"
                else:
                    source_name = "llm/" + (sources_used[0] if len(sources_used) == 1 else "+".join(sources_used))
                result.params[param] = PKValue(
                    value=fval,
                    unit=val_info.get("unit", ""),
                    source=source_name,
                    raw_text=source_text or "",
                    reasoning=reasoning,
                )
            except (ValueError, TypeError):
                pass

    return result
