"""
Стадия 2: препарат → ФК параметры.

Архитектура:
  2.0  Поиск препарата в Видаль (по торговому названию) + мост рус→лат
  2.1  Поиск вещества в Видаль (по МНН)
  2.2  Структурированные числа: e-Drug3D, OSP
  2.2b CVintra: база CVintra (PMC + OSP)
  2.3  Текстовые источники: DrugBank, ОХЛП
  2.4  LLM-валидация fuzzy-матчей
  2.5  LLM-экстракция из текстов (для недостающих)
  2.6  Мёрж: структурированные > LLM; препарат > вещество

Приоритет: данные конкретного препарата > данные вещества.
"""

from typing import Dict, List, Optional

from .models import DrugInfo, PKParams, PKValue
from .stage2_sources import edrug3d, osp, drugbank, vidal, ohlp, llm_extract, cvintra_pmc, fda_psg
from .stage2_sources.llm_extract import LLMExtractionResult, LLMValidationResult


class Stage2Result:
    def __init__(self):
        self.name_latin: Optional[str] = None

        # Поиск по ПРЕПАРАТУ (trade name)
        self.vidal_drug_result: Optional[dict] = None

        # Поиск по ВЕЩЕСТВУ (МНН)
        self.vidal_mol_result: Optional[dict] = None
        self.edrug3d_result: Optional[dict] = None
        self.osp_result: Optional[dict] = None
        self.drugbank_result: Optional[dict] = None
        self.ohlp_result: Optional[dict] = None
        self.cvintra_pmc_result: Optional[dict] = None

        # FDA PSG — дизайн исследования (Стадия 3)
        self.fda_psg_result: Optional[dict] = None

        # Валидации fuzzy
        self.validations: Dict[str, LLMValidationResult] = {}
        self.rejected_sources: Dict[str, str] = {}

        # LLM
        self.llm_result: Dict[str, PKValue] = {}
        self.llm_detail: Optional[LLMExtractionResult] = None

        # Итог
        self.pk: PKParams = PKParams()
        self.log: List[str] = []

    def add_log(self, msg: str):
        self.log.append(msg)


def find_pk_params(drug: DrugInfo, use_llm: bool = True) -> Stage2Result:
    res = Stage2Result()
    inn_ru = drug.matched_inn or drug.query_inn
    trade_name = drug.trade_names.split(";")[0].strip() if drug.trade_names else ""

    # ── 2.0 Поиск ПРЕПАРАТА в Видаль ──
    res.add_log(f"[2.0] Поиск препарата '{trade_name}' в Видаль")
    if trade_name:
        res.vidal_drug_result = vidal.search_drug(trade_name)
        if res.vidal_drug_result:
            drug_matched = res.vidal_drug_result.get("drug_name", "")
            mt = res.vidal_drug_result.get("match_type", "")
            pk_len = len(res.vidal_drug_result.get("pharmacokinetics", ""))
            res.add_log(f"  Найден: {drug_matched} → "
                        f"вещество: {res.vidal_drug_result.get('molecule_ru','')} "
                        f"({mt}, ФК: {pk_len} симв.)")
            # LLM-валидация fuzzy для препарата
            if "fuzzy" in mt:
                vr = llm_extract.validate_fuzzy_match(trade_name, drug_matched)
                res.validations["Видаль/препарат"] = vr
                if not vr.is_same:
                    res.add_log(f"    ❌ LLM: «{drug_matched}» ≠ «{trade_name}» — {vr.reason}")
                    res.rejected_sources["Видаль/препарат"] = f"{drug_matched} ({vr.reason})"
                    res.vidal_drug_result = None
                else:
                    res.add_log(f"    ✅ LLM подтвердил: «{drug_matched}» = «{trade_name}»")
            if res.vidal_drug_result and not res.name_latin:
                res.name_latin = res.vidal_drug_result.get("name_latin", "")
        else:
            res.add_log(f"  Не найден в списке препаратов Видаль")

    # ── 2.1 Поиск ВЕЩЕСТВА в Видаль ──
    res.add_log(f"[2.1] Поиск вещества '{inn_ru}' в Видаль")
    res.vidal_mol_result = vidal.search_molecule(inn_ru)
    if res.vidal_mol_result:
        mol_matched = res.vidal_mol_result.get("name_ru", "")
        mt = res.vidal_mol_result.get("match_type", "")
        pk_len = len(res.vidal_mol_result.get("pharmacokinetics", ""))
        res.add_log(f"  Найдено: {mol_matched} → {res.vidal_mol_result.get('name_latin','')} "
                    f"({mt}, ФК: {pk_len} симв., "
                    f"препаратов: {res.vidal_mol_result.get('drugs_count', 0)})")
        # LLM-валидация fuzzy для вещества
        if "fuzzy" in mt and use_llm:
            vr = llm_extract.validate_fuzzy_match(inn_ru, mol_matched)
            res.validations["Видаль/вещество"] = vr
            if not vr.is_same:
                res.add_log(f"    ❌ LLM: «{mol_matched}» ≠ «{inn_ru}» — {vr.reason}")
                res.rejected_sources["Видаль/вещество"] = f"{mol_matched} ({vr.reason})"
                res.vidal_mol_result = None
            else:
                res.add_log(f"    ✅ LLM подтвердил: «{mol_matched}» = «{inn_ru}»")
        if res.vidal_mol_result:
            res.name_latin = res.vidal_mol_result.get("name_latin", "") or res.name_latin
    else:
        res.add_log(f"  Не найдено в Видаль")

    search_names_en = set()
    if res.name_latin:
        search_names_en.add(res.name_latin)

    if not search_names_en:
        res.add_log(f"  Нет английского имени для поиска в международных базах")

    # ── 2.2 Структурированные числа ──
    res.add_log(f"[2.2] Структурированные числовые данные")

    for name in search_names_en:
        res.edrug3d_result = edrug3d.search(name)
        if res.edrug3d_result:
            res.edrug3d_result = _validate_and_log(res, "e-Drug3D", name, res.edrug3d_result, use_llm)
            if res.edrug3d_result:
                params = res.edrug3d_result.get("params", {})
                for pn, pv in params.items():
                    raw = f" (исходное: {pv.raw_text})" if pv.raw_text else ""
                    res.add_log(f"    {pn} = {pv.value} {pv.unit}{raw}")
                if "cmax_molar" in res.edrug3d_result:
                    res.add_log(f"    cmax (молярные ед.) = {res.edrug3d_result['cmax_molar']} → LLM")
            break
    else:
        res.add_log(f"  e-Drug3D: не найдено")

    for name in search_names_en:
        res.osp_result = osp.search(name)
        if res.osp_result:
            res.osp_result = _validate_and_log(res, "OSP", name, res.osp_result, use_llm)
            break
    else:
        res.add_log(f"  OSP: не найдено")

    # ── 2.2b CVintra PMC ──
    for name in search_names_en:
        res.cvintra_pmc_result = cvintra_pmc.search(name)
        if res.cvintra_pmc_result:
            res.cvintra_pmc_result = _validate_and_log(res, "CVintra/PMC", name, res.cvintra_pmc_result, use_llm)
            if res.cvintra_pmc_result:
                cv = res.cvintra_pmc_result.get("params", {}).get("cvintra_pct")
                if cv:
                    res.add_log(f"    CVintra = {cv.value}% (PMC6989220, n={res.cvintra_pmc_result.get('n_studies','')})")
            break
    else:
        res.add_log(f"  CVintra/PMC: не найдено (53 вещества)")

    # ── 2.3 Текстовые источники ──
    res.add_log(f"[2.3] Текстовые источники")

    for name in search_names_en:
        res.drugbank_result = drugbank.search(name)
        if res.drugbank_result:
            res.drugbank_result = _validate_and_log(res, "DrugBank", name, res.drugbank_result, use_llm)
            if res.drugbank_result:
                db_id = res.drugbank_result.get("drugbank_id", "")
                url = res.drugbank_result.get("url", "")
                res.add_log(f"    ID: {db_id} | URL: {url}")
            break
    else:
        res.add_log(f"  DrugBank: не найдено")

    # ── 2.3b FDA PSG — дизайн исследования (Стадия 3) ──
    if fda_psg.FDA_PSG_ENABLED and search_names_en:
        for name in search_names_en:
            psg = fda_psg.search(name)
            if psg:
                psg_mt = psg.get("match_type", "exact")
                if "fuzzy" in psg_mt and use_llm:
                    psg_matched = psg.get("substance", "")
                    vr = llm_extract.validate_fuzzy_match(name, psg_matched)
                    res.validations["FDA PSG"] = vr
                    if not vr.is_same:
                        res.add_log(f"  FDA PSG: ❌ LLM отклонил «{psg_matched}» ≠ «{name}»")
                        psg = None
                if psg:
                    res.fda_psg_result = psg
                    flags = []
                    if psg.get("is_replicated"):
                        flags.append("replicated")
                    if psg.get("is_hvd"):
                        flags.append("HVD")
                    if psg.get("is_nti"):
                        flags.append("NTI")
                    res.add_log(
                        f"  FDA PSG: «{psg.get('substance')}» "
                        f"({psg_mt}) | форма: {psg.get('dosage_form','')} | "
                        f"CVintra≥{psg.get('cvintra_threshold','?')}% | "
                        f"{'  '.join(flags) or '—'}"
                    )
                break
        else:
            res.add_log(f"  FDA PSG: не найдено")

    res.ohlp_result = ohlp.search(inn_ru, trade_name=trade_name)
    if res.ohlp_result:
        ohlp_level = res.ohlp_result.get("level", "substance")
        ohlp_mt = res.ohlp_result.get("match_type", "")
        ohlp_ms = res.ohlp_result.get("match_score", 0)
        ohlp_tn = res.ohlp_result.get("matched_trade_name", "")
        ohlp_inn = res.ohlp_result.get("matched_inn", "")
        ohlp_label = f"'{ohlp_tn}'" if ohlp_level == "drug" else f"'{ohlp_inn}'"
        sections = []
        for f in ("pk_text", "dosing_text", "contra_text", "pd_text", "storage_text"):
            txt = res.ohlp_result.get(f, "")
            if txt:
                sections.append(f"{f}:{len(txt)}")
        res.add_log(f"  ОХЛП: {ohlp_label} ({ohlp_mt}, уровень: {ohlp_level}) | {', '.join(sections)}")

        # LLM-валидация fuzzy ОХЛП
        if "fuzzy" in ohlp_mt and use_llm:
            fuzzy_query = trade_name if ohlp_level == "drug" else inn_ru
            fuzzy_matched = ohlp_tn if ohlp_level == "drug" else ohlp_inn
            vr = llm_extract.validate_fuzzy_match(fuzzy_query, fuzzy_matched)
            res.validations["ОХЛП"] = vr
            if not vr.is_same:
                res.add_log(f"    ❌ LLM: «{fuzzy_matched}» ≠ «{fuzzy_query}» — {vr.reason}")
                res.rejected_sources["ОХЛП"] = f"{fuzzy_matched} ({vr.reason})"
                res.ohlp_result = None
            else:
                res.add_log(f"    ✅ LLM подтвердил: «{fuzzy_matched}» = «{fuzzy_query}»")
    else:
        res.add_log(f"  ОХЛП: {'отключён' if not ohlp.OHLP_ENABLED else 'не найдено'}")

    # ── 2.4 LLM: отправляем ВСЕ данные, LLM выбирает лучшее ──
    res.add_log(f"[2.4] Сборка данных для LLM")

    pk = PKParams()
    all_params = ["cmax", "auc", "tmax_h", "t_half_h", "cvintra_pct"]

    if use_llm:
        texts = {}

        # [ПРЕПАРАТ] — данные конкретного торгового препарата
        if res.vidal_drug_result:
            drug_pk = res.vidal_drug_result.get("pharmacokinetics", "")
            if drug_pk:
                texts["[ПРЕПАРАТ/vidal_drug]"] = drug_pk

        if res.ohlp_result:
            pk_text = res.ohlp_result.get("pk_text", "")
            if pk_text:
                ohlp_tag = "[ПРЕПАРАТ/ohlp]" if res.ohlp_result.get("level") == "drug" else "[ВЕЩЕСТВО/ohlp]"
                texts[ohlp_tag] = pk_text

        # [ВЕЩЕСТВО] — готовые числа из структурированных баз
        if res.edrug3d_result:
            parts = []
            for pn, pv in res.edrug3d_result.get("params", {}).items():
                parts.append(f"{pn} = {pv.value} {pv.unit}")
            if "cmax_molar" in res.edrug3d_result:
                parts.append(f"cmax_molar = {res.edrug3d_result['cmax_molar']} (молярные ед., пересчитай если знаешь MW)")
            if parts:
                texts["[ВЕЩЕСТВО/edrug3d]"] = "\n".join(parts)

        if res.osp_result:
            parts = []
            for pn, pv in res.osp_result.get("params", {}).items():
                parts.append(f"{pn} = {pv.value} {pv.unit}")
            if parts:
                texts["[ВЕЩЕСТВО/osp]"] = "\n".join(parts)

        if res.cvintra_pmc_result:
            cv_parts = []
            cv_r = res.cvintra_pmc_result
            if cv_r.get("cvintra_cmax_pct"):
                cv_parts.append(f"CVintra Cmax = {cv_r['cvintra_cmax_pct']}%")
            if cv_r.get("cvintra_auc_pct"):
                cv_parts.append(f"CVintra AUC = {cv_r['cvintra_auc_pct']}%")
            if cv_r.get("n_studies"):
                cv_parts.append(f"(из {cv_r['n_studies']} BE-исследований, Park et al. 2020)")
            if cv_r.get("sample_size_80pwr"):
                cv_parts.append(f"Рекомендуемый размер выборки: {cv_r['sample_size_80pwr']} (80% power)")
            if cv_parts:
                texts["[ВЕЩЕСТВО/cvintra_pmc]"] = "\n".join(cv_parts)

        if res.fda_psg_result:
            cv_thr = res.fda_psg_result.get("cvintra_threshold")
            if cv_thr:
                texts["[ВЕЩЕСТВО/fda_psg]"] = f"CVintra threshold from FDA PSG: ≥{cv_thr}% (high variability, reference-scaled BE applies)"

        # [ВЕЩЕСТВО] — текстовые данные
        if res.vidal_mol_result:
            mol_pk = res.vidal_mol_result.get("pharmacokinetics", "")
            if mol_pk:
                texts["[ВЕЩЕСТВО/vidal_mol]"] = mol_pk

        if res.drugbank_result:
            db_parts = []
            for fld in ["absorption", "half_life", "volume_of_distribution", "clearance"]:
                txt = res.drugbank_result.get(fld, "")
                if txt:
                    db_parts.append(f"{fld}: {txt}")
            if db_parts:
                texts["[ВЕЩЕСТВО/drugbank]"] = "\n".join(db_parts)

        if texts:
            res.add_log(f"  LLM анализирует ВСЕ источники для {len(all_params)} параметров")
            res.add_log(f"  Источники: {list(texts.keys())}")

            llm_out = llm_extract.extract_pk_from_texts(texts, all_params)
            res.llm_detail = llm_out

            if llm_out.error:
                res.add_log(f"  LLM ошибка: {llm_out.error}")
            else:
                res.llm_result = llm_out.params
                for pname, pval in res.llm_result.items():
                    if hasattr(pk, pname):
                        setattr(pk, pname, pval)
                        res.add_log(f"    {pname} = {pval.value} {pval.unit} (из {pval.source})")
                        if pval.raw_text:
                            res.add_log(f"      Цитата: «{pval.raw_text[:120]}»")
        else:
            res.add_log(f"  Нет данных ни из одного источника")
    else:
        # Без LLM — fallback на структурированные числа
        res.add_log(f"[2.4] LLM отключён, берём только структурированные числа")
        if res.edrug3d_result:
            for pname, pval in res.edrug3d_result.get("params", {}).items():
                if hasattr(pk, pname):
                    setattr(pk, pname, pval)
        if res.osp_result:
            for pname, pval in res.osp_result.get("params", {}).items():
                if hasattr(pk, pname) and getattr(pk, pname) is None:
                    setattr(pk, pname, pval)
        if res.cvintra_pmc_result:
            for pname, pval in res.cvintra_pmc_result.get("params", {}).items():
                if hasattr(pk, pname) and getattr(pk, pname) is None:
                    setattr(pk, pname, pval)

    res.pk = pk

    filled = pk.filled_params()
    still_missing = pk.missing_params()
    res.add_log(f"\n  Итого: {len(filled)}/5 параметров найдено")
    if still_missing:
        res.add_log(f"  Не найдены: {', '.join(still_missing)}")

    return res


def _validate_and_log(res: Stage2Result, source_name: str, query: str,
                      result: dict, use_llm: bool) -> Optional[dict]:
    """Валидирует fuzzy-матч через LLM. Возвращает result или None если отклонён."""
    matched_name = result.get("matched_name", result.get("matched_inn", result.get("name_ru", "")))
    match_type = result.get("match_type", "")
    match_score = result.get("match_score", 0)
    n_params = len(result.get("params", {}))

    if "exact" in match_type:
        res.add_log(f"  {source_name}: '{query}' → {matched_name} (exact, {n_params} пар.)")
        return result

    res.add_log(f"  {source_name}: '{query}' → {matched_name} (fuzzy {match_score:.0f}%)")

    if use_llm:
        vr = llm_extract.validate_fuzzy_match(query, matched_name)
        res.validations[source_name] = vr
        if not vr.is_same:
            res.add_log(f"    ❌ LLM: «{matched_name}» ≠ «{query}» — {vr.reason}")
            res.rejected_sources[source_name] = f"{matched_name} ({vr.reason})"
            return None
        else:
            res.add_log(f"    ✅ LLM подтвердил: «{matched_name}» = «{query}»")

    return result
