#!/usr/bin/env python3
"""
Streamlit UI: МНН → оригинальный препарат → ФК параметры.
Две страницы: Анализ | Схема работы
"""

import streamlit as st
import os
import math
import html as html_mod

st.set_page_config(
    page_title="БиоЭкв — дизайн исследования",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.block-container { max-width: 960px; padding-top: 0.5rem; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero-title {
    text-align: center; font-size: 2rem; font-weight: 800;
    background: linear-gradient(135deg, #0ea5e9, #6366f1, #a855f7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0.5rem 0 0.2rem 0;
}
.hero-sub { text-align: center; color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; }

.stage-header {
    background: linear-gradient(135deg, #0f172a, #1e293b); color: white;
    padding: 0.7rem 1.2rem; border-radius: 10px; margin: 1.5rem 0 0.8rem 0;
    font-size: 1.05rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;
}
.stage-num {
    background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white;
    padding: 0.15rem 0.55rem; border-radius: 6px; font-size: 0.8rem; font-weight: 800;
}

.drug-card {
    background: linear-gradient(135deg, #f0f9ff, #eff6ff);
    border: 1px solid #bae6fd; border-left: 5px solid #0ea5e9;
    padding: 1.2rem 1.4rem; border-radius: 0 12px 12px 0; margin: 0.5rem 0;
}
.drug-card-warn {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 1px solid #fde68a; border-left: 5px solid #f59e0b;
    padding: 1.2rem 1.4rem; border-radius: 0 12px 12px 0; margin: 0.5rem 0;
}
.drug-name { font-size: 1.3rem; font-weight: 800; color: #0f172a; margin: 0.3rem 0; }
.drug-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }

.pill { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
.pill-green { background: #dcfce7; color: #166534; }
.pill-red { background: #fee2e2; color: #991b1b; }
.pill-gray { background: #f1f5f9; color: #64748b; }
.pill-purple { background: #f3e8ff; color: #6b21a8; }
.pill-yellow { background: #fef9c3; color: #854d0e; }
.pill-blue { background: #dbeafe; color: #1e40af; }

.pk-table {
    width: 100%; border-collapse: separate; border-spacing: 0;
    margin: 0.5rem 0; border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0;
}
.pk-table th {
    background: linear-gradient(135deg, #0f172a, #1e293b); color: white;
    padding: 0.6rem 1rem; text-align: left; font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.pk-table td { padding: 0.6rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.88rem; }
.pk-table tr:last-child td { border-bottom: none; }
.pk-table tr:nth-child(even) { background: #f8fafc; }
.pk-found { color: #059669; font-weight: 700; }
.pk-llm { color: #7c3aed; font-weight: 700; }
.pk-miss { color: #cbd5e1; }

.metric-card {
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; text-align: center;
}
.metric-value { font-size: 1.6rem; font-weight: 800; color: #0f172a; }
.metric-label { font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; }

.code-box {
    background: #1e1b4b; color: #e2e8f0; border-radius: 8px; padding: 0.8rem 1rem;
    font-family: 'Menlo', monospace; font-size: 0.76rem; line-height: 1.5;
    max-height: 300px; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
}
.text-block {
    font-size: 0.82rem; color: #374151; background: #f8fafc; padding: 0.5rem 0.7rem;
    border-radius: 6px; max-height: 180px; overflow-y: auto; border: 1px solid #e2e8f0;
}

a.src-link { color: #2563eb; text-decoration: none; font-size: 0.8rem; }
a.src-link:hover { text-decoration: underline; }

.all-data-row {
    display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.7rem;
    border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; flex-wrap: wrap;
}
.all-data-row:last-child { border-bottom: none; }
.chosen-row { background: #f0fdf4; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

banner_path = os.path.join(os.path.dirname(__file__), "assets", "banner.png")
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)

st.markdown('<div class="hero-title">Автоматизация дизайна исследований биоэквивалентности</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Введите МНН — система найдёт оригинальный препарат и соберёт ФК параметры из 7 баз данных + LLM</div>', unsafe_allow_html=True)

if "current_inn" not in st.session_state:
    st.session_state["current_inn"] = ""
if "current_form" not in st.session_state:
    st.session_state["current_form"] = ""

col_input, col_form, col_btn, col_ex = st.columns([3, 2, 1, 1])
with col_input:
    inn_query = st.text_input("МНН", value=st.session_state["current_inn"],
                              placeholder="амлодипин, ибупрофен, метформин ...", label_visibility="collapsed")
with col_form:
    form_query = st.text_input("Форма (необязательно)", value=st.session_state["current_form"],
                               placeholder="таблетки, капсулы, раствор ...", label_visibility="collapsed")
with col_btn:
    st.markdown("<div style='height: 0.1rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("🔍 Найти", type="primary", use_container_width=True)
with col_ex:
    st.markdown("<div style='height: 0.1rem'></div>", unsafe_allow_html=True)
    if st.button("📋 Примеры", use_container_width=True):
        st.session_state["show_examples"] = not st.session_state.get("show_examples", False)
        st.rerun()

if inn_query:
    st.session_state["current_inn"] = inn_query
if form_query:
    st.session_state["current_form"] = form_query

_EXAMPLE_GROUPS = {
    "🫀 Сердечно-сосудистые": [
        "амлодипин", "лозартан", "бисопролол", "эналаприл", "аторвастатин",
        "валсартан", "нифедипин", "метопролол", "каптоприл", "розувастатин",
    ],
    "💊 НПВС / анальгетики": [
        "ибупрофен", "парацетамол", "диклофенак", "кеторолак", "мелоксикам",
        "напроксен", "целекоксиб", "индометацин", "нимесулид", "кетопрофен",
    ],
    "🧬 Эндокринология": [
        "метформин", "вилдаглиптин", "левотироксин", "глимепирид", "дапаглифлозин",
        "гликлазид", "симвастатин", "пиоглитазон",
    ],
    "🦠 Антибиотики / противовирусные": [
        "амоксициллин", "азитромицин", "ципрофлоксацин", "осельтамивир", "флуконазол",
        "кларитромицин", "левофлоксацин", "метронидазол", "доксициклин",
    ],
    "🧠 ЦНС / ЖКТ": [
        "омепразол", "пантопразол", "сертралин", "карбамазепин", "габапентин",
        "ламотриджин", "эсциталопрам", "рисперидон",
    ],
    "📋 Есть в OSP (клинические данные)": [
        "буспирон", "мидазолам", "верапамил", "дигоксин", "кетоконазол",
        "кофеин", "эфавиренз", "дабигатран", "вориконазол",
    ],
}

if st.session_state.get("show_examples", not inn_query):
    with st.expander("📋 Примеры для тестирования (54 препарата)", expanded=True):
        for group_name, examples in _EXAMPLE_GROUPS.items():
            st.markdown(f"**{group_name}**")
            n_cols = min(len(examples), 5)
            rows_of_examples = [examples[i:i+n_cols] for i in range(0, len(examples), n_cols)]
            for row_ex in rows_of_examples:
                cols = st.columns(n_cols)
                for col, ex in zip(cols, row_ex):
                    with col:
                        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                            st.session_state["current_inn"] = ex
                            st.session_state["show_examples"] = False
                            st.rerun()

if not inn_query:
    st.stop()

from pipeline.stage1 import find_all_by_inn
from pipeline.stage2 import Stage2Result, _validate_and_log
from pipeline.stage2_sources import edrug3d, osp, drugbank, vidal, ohlp, llm_extract, cvintra_pmc, fda_psg
from pipeline.stage2_sources.ohlp import OHLP_ENABLED
from pipeline.models import PK_PARAM_LABELS, PKParams, PKValue
from pipeline.config import DEEPSEEK_API_KEY, FDA_PSG_ENABLED

use_llm = bool(DEEPSEEK_API_KEY)

SOURCE_LABELS = {
    "llm/vidal_drug": ("Видаль — страница препарата", "pill-green"),
    "llm/ohlp": ("ОХЛП (PDF)", "pill-green"),
    "llm/edrug3d": ("e-Drug3D — числа вещества", "pill-purple"),
    "llm/osp": ("OSP — числа вещества", "pill-purple"),
    "llm/drugbank": ("DrugBank — текст вещества", "pill-purple"),
    "llm/vidal_mol": ("Видаль — страница вещества", "pill-purple"),
    "llm/fda_psg": ("FDA PSG — дизайн (FDA)", "pill-blue"),
    "edrug3d": ("e-Drug3D", "pill-green"),
    "osp": ("OSP", "pill-green"),
}


def _source_label(source: str) -> str:
    return SOURCE_LABELS.get(source, (source, "pill-gray"))[0]


def _get_source_url(val_source, s2_res):
    if "vidal_drug" in val_source and s2_res.vidal_drug_result:
        _dn = s2_res.vidal_drug_result.get("drug_name", "").replace(" ", "+")
        return s2_res.vidal_drug_result.get("drug_url", "") or f"https://www.vidal.ru/search?t=all&q={_dn}"
    if "vidal_mol" in val_source and s2_res.vidal_mol_result:
        return s2_res.vidal_mol_result.get("url", "")
    if "drugbank" in val_source and s2_res.drugbank_result:
        return s2_res.drugbank_result.get("url", "")
    return ""


def _plural(n: int, one: str, few: str, many: str) -> str:
    """Склонение: 1 секция, 2 секции, 5 секций."""
    n_abs = abs(n) % 100
    if 11 <= n_abs <= 19:
        return f"{n} {many}"
    last = n_abs % 10
    if last == 1:
        return f"{n} {one}"
    if 2 <= last <= 4:
        return f"{n} {few}"
    return f"{n} {many}"

def _esc(text: str) -> str:
    return html_mod.escape(text) if text else ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СТАДИЯ 1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_form_label = f" + {form_query}" if form_query else ""
st.markdown(f'<div class="stage-header"><span class="stage-num">1</span> МНН{_form_label} → Оригинальный препарат</div>', unsafe_allow_html=True)

with st.status("Поиск в реестре ЕАЭС...", expanded=True) as status_s1:
    all_matches = find_all_by_inn(inn_query, query_form=form_query, use_llm=use_llm)

    if not all_matches:
        status_s1.update(label="МНН не найден", state="error")
        st.error(f"МНН **«{inn_query}»** не найден в реестре ЕАЭС.")
        st.stop()

    originals = [d for d in all_matches if d.drug_kind == "оригинальный"]
    drug = originals[0] if originals else all_matches[0]

    if all_matches[0].match_type == "fuzzy":
        st.warning(f"Нечёткое совпадение: **{all_matches[0].matched_inn}** ({all_matches[0].match_score:.0f}%)")

    with st.expander(f"Все совпадения в реестре ({len(all_matches)})", expanded=False):
        rows_data = []
        for d in all_matches:
            names = d.trade_names if len(d.trade_names) <= 60 else d.trade_names[:57] + "..."
            kind_display = ("⭐ " + d.drug_kind) if d.drug_kind == "оригинальный" else d.drug_kind
            form_short = d.dosage_form[:40] + "…" if len(d.dosage_form) > 40 else d.dosage_form
            rows_data.append({"Тип": kind_display, "Торговые наименования": names,
                              "Форма": form_short or "—",
                              "Совпадение": d.match_type if d.match_type == "exact" else f"fuzzy ({d.match_score:.0f}%)"})
        st.dataframe(rows_data, use_container_width=True, hide_index=True)

    card_class = "drug-card" if originals else "drug-card-warn"
    label_text = "ОРИГИНАЛЬНЫЙ ПРЕПАРАТ" if originals else f"ОРИГИНАЛЬНЫЙ НЕ НАЙДЕН ({drug.drug_kind.upper()})"

    _td = 'style="color: #64748b; padding-right: 1rem; font-weight:500;"'
    _rows = [f'<tr><td {_td}>МНН</td><td><strong>{_esc(drug.matched_inn)}</strong></td></tr>']
    if drug.dosage_form:
        _rows.append(f'<tr><td {_td}>Форма</td><td>{_esc(drug.dosage_form)}</td></tr>')
    _rows.append(f'<tr><td {_td}>АТХ</td><td>{_esc(drug.atc_code)}</td></tr>')
    _rows.append(f'<tr><td {_td}>Держатель РУ</td><td>{_esc(drug.holders)}</td></tr>')
    _rows.append(f'<tr><td {_td}>Страны</td><td>{_esc(drug.countries)}</td></tr>')
    _table_rows = "".join(_rows)
    st.markdown(
        f'<div class="{card_class}">'
        f'<div class="drug-label">{label_text}</div>'
        f'<div class="drug-name">{_esc(drug.trade_names)}</div>'
        f'<table style="margin-top: 0.3rem; font-size: 0.88rem;">{_table_rows}</table>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('[↗ Реестр ЕАЭС](https://portal.eaeunion.org/sites/commonprocesses/ru-ru/Pages/DrugRegistrationDetails.aspx/RegistryCard.aspx)')

    n_orig = len(originals)
    status_s1.update(label=f"Найдено: {drug.matched_inn} ({len(all_matches)} записей, {n_orig} оригин.)", state="complete")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СТАДИЯ 2
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="stage-header"><span class="stage-num">2</span> Сбор ФК параметров из всех источников</div>', unsafe_allow_html=True)

s2 = Stage2Result()
inn_ru = drug.matched_inn or drug.query_inn
trade_name = drug.trade_names.split(";")[0].strip() if drug.trade_names else ""

# ── 2.0 Видаль: препарат ──
with st.status("🏷️ Поиск препарата в Видале...", expanded=False) as st_vidal_drug:
    if trade_name:
        s2.vidal_drug_result = vidal.search_drug(trade_name)
        # LLM-валидация fuzzy для препарата
        if s2.vidal_drug_result and "fuzzy" in s2.vidal_drug_result.get("match_type", "") and use_llm:
            drug_matched = s2.vidal_drug_result.get("drug_name", "")
            vr = llm_extract.validate_fuzzy_match(trade_name, drug_matched)
            s2.validations["Видаль/препарат"] = vr
            if not vr.is_same:
                s2.rejected_sources["Видаль/препарат"] = f"{drug_matched} ({vr.reason})"
                s2.vidal_drug_result = None
        if s2.vidal_drug_result and not s2.name_latin:
            s2.name_latin = s2.vidal_drug_result.get("name_latin", "")

    if s2.vidal_drug_result:
        vdr = s2.vidal_drug_result
        _drug_name_for_url = vdr.get("drug_name", "").replace(" ", "+")
        drug_url = vdr.get("drug_url", "") or f"https://www.vidal.ru/search?t=all&q={_drug_name_for_url}"
        pk_len = len(vdr.get("pharmacokinetics", ""))
        mt = vdr.get("match_type", "")
        match_badge = f' <span class="pill pill-yellow">fuzzy {vdr.get("match_score",0):.0f}%</span>' if "fuzzy" in mt else ""
        st.markdown(f'{match_badge} **{_esc(vdr["drug_name"])}** → вещество: {_esc(vdr.get("molecule_ru", "—"))}', unsafe_allow_html=True)
        if pk_len:
            st.markdown(f'ФК текст: {pk_len} символов')
            with st.expander("Текст фармакокинетики", expanded=False):
                st.markdown(f'<div class="text-block">{_esc(vdr.get("pharmacokinetics",""))}</div>', unsafe_allow_html=True)
        st.markdown(f'[↗ Открыть на Видале]({drug_url or "https://www.vidal.ru"})')
        st_vidal_drug.update(label=f"🏷️ Видаль (препарат): {vdr['drug_name']} (ФК: {pk_len} симв.)", state="complete")
    elif s2.rejected_sources.get("Видаль/препарат"):
        st_vidal_drug.update(label=f"🏷️ Видаль (препарат): ❌ отклонён LLM", state="complete")
    else:
        st_vidal_drug.update(label="🏷️ Видаль (препарат): не найден", state="complete")

# ── 2.1 Видаль: вещество ──
with st.status("🧬 Поиск вещества в Видале...", expanded=False) as st_vidal_mol:
    s2.vidal_mol_result = vidal.search_molecule(inn_ru)
    # LLM-валидация fuzzy для вещества
    if s2.vidal_mol_result and "fuzzy" in s2.vidal_mol_result.get("match_type", "") and use_llm:
        mol_matched = s2.vidal_mol_result.get("name_ru", "")
        vr = llm_extract.validate_fuzzy_match(inn_ru, mol_matched)
        s2.validations["Видаль/вещество"] = vr
        if not vr.is_same:
            s2.rejected_sources["Видаль/вещество"] = f"{mol_matched} ({vr.reason})"
            s2.vidal_mol_result = None
    if s2.vidal_mol_result:
        s2.name_latin = s2.vidal_mol_result.get("name_latin", "") or s2.name_latin
    search_names_en = set()
    if s2.name_latin:
        search_names_en.add(s2.name_latin)

    if s2.vidal_mol_result:
        vmr = s2.vidal_mol_result
        pk_len = len(vmr.get("pharmacokinetics", ""))
        mt = vmr.get("match_type", "")
        match_badge = f' <span class="pill pill-yellow">fuzzy {vmr.get("match_score",0):.0f}%</span>' if "fuzzy" in mt else ""
        st.markdown(f'{match_badge} **{_esc(vmr["name_ru"])}** → {_esc(vmr.get("name_latin", "—"))} (ФК: {pk_len} симв.)', unsafe_allow_html=True)
        pk_text = vmr.get("pharmacokinetics", "")
        if pk_text:
            with st.expander("Текст фармакокинетики", expanded=False):
                st.markdown(f'<div class="text-block">{_esc(pk_text)}</div>', unsafe_allow_html=True)
        url = vmr.get("url", "") or "https://www.vidal.ru"
        st.markdown(f'[↗ Открыть на Видале]({url})')
        st_vidal_mol.update(label=f"🧬 Видаль (вещество): {vmr['name_ru']} → {vmr.get('name_latin','—')}", state="complete")
    elif s2.rejected_sources.get("Видаль/вещество"):
        st_vidal_mol.update(label=f"🧬 Видаль (вещество): ❌ отклонён LLM", state="complete")
    else:
        st_vidal_mol.update(label="🧬 Видаль (вещество): не найдено", state="complete")

# ── 2.2 ОХЛП ──
with st.status("📄 ОХЛП...", expanded=False) as st_ohlp:
    s2.ohlp_result = ohlp.search(inn_ru, trade_name=trade_name)

    if s2.ohlp_result and "fuzzy" in s2.ohlp_result.get("match_type", "") and use_llm:
        ohlp_level = s2.ohlp_result.get("level", "substance")
        fuzzy_query = trade_name if ohlp_level == "drug" else inn_ru
        fuzzy_matched = s2.ohlp_result.get("matched_trade_name", "") if ohlp_level == "drug" else s2.ohlp_result.get("matched_inn", "")
        vr = llm_extract.validate_fuzzy_match(fuzzy_query, fuzzy_matched)
        s2.validations["ОХЛП"] = vr
        if not vr.is_same:
            s2.rejected_sources["ОХЛП"] = f"{fuzzy_matched} ({vr.reason})"
            s2.ohlp_result = None

    _OHLP_SECTIONS_ALL = [
        ("composition_text", "2. Состав"),
        ("form_text", "3. Лекарственная форма"),
        ("indications_text", "4.1 Показания"),
        ("dosing_text", "4.2 Дозирование"),
        ("contra_text", "4.3 Противопоказания"),
        ("precautions_text", "4.4 Особые указания"),
        ("interactions_text", "4.5 Взаимодействия"),
        ("pregnancy_text", "4.6 Беременность/лактация"),
        ("adverse_text", "4.8 Нежелательные реакции"),
        ("overdose_text", "4.9 Передозировка"),
        ("pd_text", "5.1 Фармакодинамика"),
        ("pk_text", "5.2 Фармакокинетика"),
        ("excipients_text", "6.1 Вспомогательные вещества"),
        ("shelf_life_text", "6.3 Срок годности"),
        ("storage_text", "6.4 Хранение"),
    ]
    _OHLP_PK_SECTIONS = [
        ("pk_text", "5.2 Фармакокинетика"),
        ("pd_text", "5.1 Фармакодинамика"),
    ]
    if s2.ohlp_result:
        ohlp_inn = s2.ohlp_result.get("matched_inn", "—")
        ohlp_tn = s2.ohlp_result.get("matched_trade_name", "")
        ohlp_level = s2.ohlp_result.get("level", "substance")
        ohlp_mt = s2.ohlp_result.get("match_type", "")
        pk_count = sum(1 for fn, _ in _OHLP_PK_SECTIONS if s2.ohlp_result.get(fn, ""))

        if ohlp_level == "drug":
            level_badge = '<span class="pill pill-green">💊 препарат</span>'
            title = f"**{ohlp_tn}** (МНН: {ohlp_inn})"
        else:
            level_badge = '<span class="pill pill-purple">🧬 вещество</span>'
            title = f"**{ohlp_inn}** (препарат: {ohlp_tn})"

        match_badge = ""
        if "fuzzy" in ohlp_mt:
            match_badge = f' <span class="pill pill-yellow">fuzzy {s2.ohlp_result.get("match_score", 0):.0f}%</span>'

        st.markdown(f'{level_badge}{match_badge} {title}', unsafe_allow_html=True)
        for fn, fl in _OHLP_PK_SECTIONS:
            txt = s2.ohlp_result.get(fn, "")
            if txt:
                with st.expander(f"{fl} ({len(txt)} симв.)", expanded=False):
                    st.markdown(f'<div class="text-block">{_esc(txt)}</div>', unsafe_allow_html=True)
        st.markdown('[↗ Реестр ОХЛП ЕАЭС](https://lk.regmed.ru/Register/EAEU_SmPC)')
        level_label = "препарат" if ohlp_level == "drug" else "МНН"
        st_ohlp.update(label=f"📄 ОХЛП ({level_label}): {ohlp_tn or ohlp_inn} (ФК: {pk_count})", state="complete")
    elif not OHLP_ENABLED:
        st_ohlp.update(label="📄 ОХЛП: PDF не распарсены", state="complete")
    else:
        st_ohlp.update(label="📄 ОХЛП: не найдено", state="complete")

# ── 2.3 e-Drug3D ──
with st.status("📊 e-Drug3D...", expanded=False) as st_ed:
    for name in search_names_en:
        s2.edrug3d_result = edrug3d.search(name)
        if s2.edrug3d_result:
            s2.edrug3d_result = _validate_and_log(s2, "e-Drug3D", name, s2.edrug3d_result, use_llm)
            break
    if s2.edrug3d_result:
        params = s2.edrug3d_result.get("params", {})
        matched = s2.edrug3d_result.get("matched_name", "—")
        parts = [f"{PK_PARAM_LABELS.get(k,(k,''))[0]}={v.value} {v.unit}" for k,v in params.items()]
        st.markdown(f'**{matched}**: {", ".join(parts) if parts else "нет числовых данных"}')
        st.markdown('[↗ e-Drug3D](https://chemoinfo.ipmc.cnrs.fr/TMP/tmp.81675/e-Drug3D_2162_PK.txt)')
        st_ed.update(label=f"📊 e-Drug3D: {matched} ({len(params)} пар.)", state="complete")
    else:
        st_ed.update(label="📊 e-Drug3D: не найдено", state="complete")

# ── 2.4 DrugBank ──
with st.status("💊 DrugBank...", expanded=False) as st_db:
    for name in search_names_en:
        s2.drugbank_result = drugbank.search(name)
        if s2.drugbank_result:
            s2.drugbank_result = _validate_and_log(s2, "DrugBank", name, s2.drugbank_result, use_llm)
            break
    if s2.drugbank_result:
        dbr = s2.drugbank_result
        matched = dbr.get("matched_name", "—")
        db_url = dbr.get("url", "")
        _DB_PK_FIELDS = [("absorption", "Absorption"), ("half_life", "Half-life")]
        pk_count = sum(1 for fn, _ in _DB_PK_FIELDS if dbr.get(fn, "").strip())
        st.markdown(f'**{matched}**')
        for fn, fl in _DB_PK_FIELDS:
            txt = dbr.get(fn, "")
            if txt and len(txt) > 10:
                with st.expander(fl, expanded=False):
                    st.markdown(f'<div class="text-block">{_esc(txt)}</div>', unsafe_allow_html=True)
        st.markdown(f'[↗ DrugBank]({db_url or "https://go.drugbank.com"})')
        st_db.update(label=f"💊 DrugBank: {matched} ({pk_count} ФК)", state="complete")
    else:
        st_db.update(label="💊 DrugBank: не найдено", state="complete")

# ── 2.5 OSP ──
with st.status("📋 OSP...", expanded=False) as st_osp:
    for name in search_names_en:
        s2.osp_result = osp.search(name)
        if s2.osp_result:
            s2.osp_result = _validate_and_log(s2, "OSP", name, s2.osp_result, use_llm)
            break
    if s2.osp_result:
        params = s2.osp_result.get("params", {})
        matched = s2.osp_result.get("matched_name", "—")
        parts = [f"{PK_PARAM_LABELS.get(k,(k,''))[0]}={v.value} {v.unit}" for k,v in params.items()]
        st.markdown(f'**{matched}**: {", ".join(parts)}')
        st.markdown('[↗ Open Systems Pharmacology](https://www.open-systems-pharmacology.org/)')
        st_osp.update(label=f"📋 OSP: {matched} ({len(params)} пар.)", state="complete")
    else:
        st_osp.update(label="📋 OSP: не найдено", state="complete")

# ── 2.6 FDA PSG ──
with st.status("🇺🇸 FDA PSG...", expanded=False) as st_fda:
    if FDA_PSG_ENABLED and search_names_en:
        for _name in search_names_en:
            _psg = fda_psg.search(_name)
            if _psg:
                _psg_mt = _psg.get("match_type", "exact")
                if "fuzzy" in _psg_mt and use_llm:
                    _psg_matched = _psg.get("substance", "")
                    _vr = llm_extract.validate_fuzzy_match(_name, _psg_matched)
                    s2.validations["FDA PSG"] = _vr
                    if not _vr.is_same:
                        s2.rejected_sources["FDA PSG"] = f"{_psg_matched} ({_vr.reason})"
                        _psg = None
                if _psg:
                    s2.fda_psg_result = _psg
                break

    if s2.fda_psg_result:
        _p = s2.fda_psg_result
        _flags = []
        if _p.get("is_replicated"):
            _flags.append('<span class="pill pill-yellow">replicated design</span>')
        if _p.get("is_hvd"):
            _flags.append('<span class="pill pill-yellow">HVD ≥30%</span>')
        if _p.get("is_nti"):
            _flags.append('<span class="pill pill-red">NTI</span>')
        _match_badge = ""
        if "fuzzy" in _p.get("match_type", ""):
            _match_badge = f' <span class="pill pill-yellow">fuzzy {_p.get("match_score", 0):.0f}%</span>'

        st.markdown(
            f'**{_p.get("substance")}**{_match_badge} — {_p.get("form_route", "")} '
            f'{"  ".join(_flags)}',
            unsafe_allow_html=True
        )
        _cols = st.columns(3)
        _cols[0].metric("Исследований", _p.get("num_studies", 0))
        _cols[1].metric("Сила", _p.get("strength", "—"))
        _cols[2].metric("CVintra порог", f'≥{_p["cvintra_threshold"]}%' if _p.get("cvintra_threshold") else "не указан")

        if _p.get("analytes"):
            st.caption(f"Аналиты: {_p['analytes']}")
        _fda_link = _p.get("pdf_url", "") or "https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm"
        st.markdown(f'[↗ FDA PSG]({_fda_link})')

        _label_flags = []
        if _p.get("is_replicated"):
            _label_flags.append("replicated")
        if _p.get("is_nti"):
            _label_flags.append("NTI")
        _extra = f" [{', '.join(_label_flags)}]" if _label_flags else ""
        st_fda.update(
            label=f"🇺🇸 FDA PSG: {_p.get('substance', '')} ({_p.get('dosage_form', '')}){_extra}",
            state="complete"
        )
    elif not FDA_PSG_ENABLED:
        st_fda.update(label="🇺🇸 FDA PSG: база не загружена", state="complete")
    else:
        st_fda.update(label="🇺🇸 FDA PSG: не найдено", state="complete")

# ── 2.7 CVintra/PMC (BE-исследования) ──
with st.status("📊 CVintra/PMC...", expanded=False) as st_cv_pmc:
    for name in search_names_en:
        s2.cvintra_pmc_result = cvintra_pmc.search(name)
        if s2.cvintra_pmc_result:
            s2.cvintra_pmc_result = _validate_and_log(s2, "CVintra/PMC", name, s2.cvintra_pmc_result, use_llm)
            break
    if s2.cvintra_pmc_result:
        cvr = s2.cvintra_pmc_result
        matched = cvr.get("matched_name", "—")
        cv_cmax = cvr.get("cvintra_cmax_pct")
        cv_auc = cvr.get("cvintra_auc_pct")
        n = cvr.get("n_studies", "")
        ss80 = cvr.get("sample_size_80pwr", "")
        ss90 = cvr.get("sample_size_90pwr", "")
        parts = []
        if cv_cmax:
            parts.append(f"**Cmax CV = {cv_cmax}%**")
        if cv_auc:
            parts.append(f"AUC CV = {cv_auc}%")
        if n:
            parts.append(f"из {n} BE-исследований (pooled)")
        st.markdown(f'{matched}: {" | ".join(parts)}')
        if ss80:
            st.markdown(f'Рекомендуемый размер выборки: **{ss80}** (80% power) / **{ss90}** (90% power)')
        ref_url = cvr.get("reference_url", "") or "https://pmc.ncbi.nlm.nih.gov/articles/PMC6989220/"
        ref_text = cvr.get("reference", "") or "Park et al. 2020 (PMC)"
        st.markdown(f'[↗ {ref_text}]({ref_url})')
        st_cv_pmc.update(label=f"📊 CVintra/PMC: {cv_cmax or cv_auc}% ({matched}, n={n})", state="complete")
    else:
        st_cv_pmc.update(label="📊 CVintra/PMC: не найдено", state="complete")

# ── 2.8 CVintra/OSP (клинические PK) ──
osp_cv = s2.osp_result.get("params", {}).get("cvintra_pct") if s2.osp_result else None
with st.status("📊 CVintra/OSP...", expanded=False) as st_cv_osp:
    if osp_cv:
        matched_osp = s2.osp_result.get("matched_name", "—")
        st.markdown(f'{matched_osp}: **Cmax CV = {osp_cv.value}%** (медиана по исследованиям)')
        st.caption(osp_cv.raw_text)
        st.markdown('[↗ Open Systems Pharmacology](https://www.open-systems-pharmacology.org/)')
        st_cv_osp.update(label=f"📊 CVintra/OSP: {osp_cv.value}% ({matched_osp})", state="complete")
    else:
        st_cv_osp.update(label="📊 CVintra/OSP: нет CV данных", state="complete")

# ── Rejected fuzzy ──
if s2.rejected_sources:
    st.markdown("##### ❌ Отклонённые fuzzy-матчи (LLM)")
    for src, reason in s2.rejected_sources.items():
        st.markdown(f'<span class="pill pill-yellow">отклонён</span> **{src}**: {reason}', unsafe_allow_html=True)

if s2.validations:
    with st.expander("🔍 Детали LLM-валидаций fuzzy-матчей", expanded=False):
        for src, vr in s2.validations.items():
            icon = "✅" if vr.is_same else "❌"
            st.markdown(f"**{src}**: {icon} {vr.reason}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СВОДНАЯ ТАБЛИЦА ВСЕХ ДАННЫХ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="stage-header"><span class="stage-num">⚖</span> Все собранные данные</div>', unsafe_allow_html=True)
st.caption("Все найденные значения из всех источников. LLM выберет лучшее для каждого параметра.")

all_collected = {}
param_names = ["cmax", "auc", "tmax_h", "t_half_h", "cvintra_pct"]

def _add_collected(source_tag: str, source_label: str, level: str, params_dict: dict, url: str = ""):
    for pn, pv in params_dict.items():
        if pn not in all_collected:
            all_collected[pn] = []
        all_collected[pn].append({
            "source_tag": source_tag,
            "source_label": source_label,
            "level": level,
            "value": pv.value,
            "unit": pv.unit,
            "raw_text": pv.raw_text,
            "url": url,
        })

def _add_text_source(source_tag: str, source_label: str, level: str, text: str, url: str = ""):
    """Register text-only source (no extracted numbers yet — LLM will extract)."""
    if not text or not text.strip():
        return
    for pn in param_names:
        if pn not in all_collected:
            all_collected[pn] = []
        all_collected[pn].append({
            "source_tag": source_tag,
            "source_label": source_label,
            "level": level,
            "value": None,
            "unit": "",
            "raw_text": text,
            "url": url,
            "text_only": True,
        })

if s2.edrug3d_result:
    _add_collected("edrug3d", "e-Drug3D", "вещество", s2.edrug3d_result.get("params", {}))

if s2.osp_result:
    _add_collected("osp", "OSP", "вещество", s2.osp_result.get("params", {}))

if s2.cvintra_pmc_result:
    _add_collected("cvintra_pmc", "CVintra/PMC", "вещество", s2.cvintra_pmc_result.get("params", {}))

if s2.vidal_drug_result:
    drug_pk = s2.vidal_drug_result.get("pharmacokinetics", "")
    _dn = s2.vidal_drug_result.get("drug_name", "").replace(" ", "+")
    drug_url = s2.vidal_drug_result.get("drug_url", "") or f"https://www.vidal.ru/search?t=all&q={_dn}"
    if drug_pk:
        _add_text_source("vidal_drug", "Видаль (препарат)", "препарат", drug_pk, drug_url)

if s2.ohlp_result:
    ohlp_pk = s2.ohlp_result.get("pk_text", "")
    if ohlp_pk:
        ohlp_lvl = "препарат" if s2.ohlp_result.get("level") == "drug" else "вещество"
        _add_text_source("ohlp", f"ОХЛП ({s2.ohlp_result.get('matched_trade_name', '')})", ohlp_lvl, ohlp_pk)

if s2.vidal_mol_result:
    mol_pk = s2.vidal_mol_result.get("pharmacokinetics", "")
    mol_url = s2.vidal_mol_result.get("url", "")
    if mol_pk:
        _add_text_source("vidal_mol", "Видаль (вещество)", "вещество", mol_pk, mol_url)

if s2.drugbank_result:
    db_url = s2.drugbank_result.get("url", "")
    db_texts = []
    for fld in ["absorption", "half_life", "volume_of_distribution", "clearance"]:
        t = s2.drugbank_result.get(fld, "")
        if t:
            db_texts.append(f"{fld}: {t}")
    if db_texts:
        _add_text_source("drugbank", "DrugBank", "вещество", "\n".join(db_texts), db_url)

if s2.fda_psg_result:
    fda_summary_parts = []
    if s2.fda_psg_result.get("cvintra_threshold"):
        fda_summary_parts.append(f"CVintra ≥{s2.fda_psg_result['cvintra_threshold']}%")
    if s2.fda_psg_result.get("is_replicated"):
        fda_summary_parts.append("replicated design")
    if s2.fda_psg_result.get("is_nti"):
        fda_summary_parts.append("NTI")
    if s2.fda_psg_result.get("design_fasting"):
        fda_summary_parts.append(s2.fda_psg_result["design_fasting"][:120])
    if fda_summary_parts:
        _add_text_source(
            "fda_psg", f"FDA PSG ({s2.fda_psg_result.get('substance','')})",
            "вещество", " | ".join(fda_summary_parts),
            s2.fda_psg_result.get("pdf_url", "")
        )

for pn in param_names:
    label, unit = PK_PARAM_LABELS[pn]
    entries = all_collected.get(pn, [])
    number_entries = [e for e in entries if e.get("value") is not None]
    text_entries = [e for e in entries if e.get("text_only")]

    if not number_entries and not text_entries:
        st.markdown(f'<div class="all-data-row"><strong>{label}</strong> <span class="pill pill-gray">нет данных ни в одном источнике</span></div>', unsafe_allow_html=True)
        continue

    parts_html = f'<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:0.5rem 0; margin:0.3rem 0;">'
    parts_html += f'<div style="padding:0.3rem 0.7rem; font-weight:700; border-bottom:1px solid #e2e8f0;">{label} ({unit})</div>'

    for e in number_entries:
        level_icon = "💊" if e["level"] == "препарат" else "🧬"
        val_str = f"{e['value']:,.2f}" if e['value'] < 10000 else f"{e['value']:,.0f}"
        url_link = f' <a href="{e["url"]}" target="_blank" style="color:#2563eb; font-size:0.75rem;">↗</a>' if e.get("url") else ""
        raw = f' <span style="color:#94a3b8; font-size:0.75rem;">← {_esc(e["raw_text"])}</span>' if e.get("raw_text") else ""
        parts_html += f'<div class="all-data-row">{level_icon} <span class="pill pill-blue">{e["source_label"]}</span> <b>{val_str} {e["unit"]}</b>{raw}{url_link}</div>'

    for e in text_entries:
        if e["source_tag"] in [ne["source_tag"] for ne in number_entries]:
            continue
        level_icon = "💊" if e["level"] == "препарат" else "🧬"
        url_link = f' <a href="{e["url"]}" target="_blank" style="color:#2563eb; font-size:0.75rem;">↗</a>' if e.get("url") else ""
        parts_html += f'<div class="all-data-row">{level_icon} <span class="pill pill-gray">{e["source_label"]}</span> <i style="color:#94a3b8; font-size:0.8rem;">текст — LLM извлечёт число</i>{url_link}</div>'

    parts_html += '</div>'
    st.markdown(parts_html, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM: выбор лучших значений
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="stage-header"><span class="stage-num">🤖</span> LLM выбирает лучшие параметры</div>', unsafe_allow_html=True)

pk = PKParams()

if use_llm:
    with st.status("🤖 LLM анализирует все источники...", expanded=True) as st_llm:
        texts = {}
        if s2.vidal_drug_result:
            dp = s2.vidal_drug_result.get("pharmacokinetics", "")
            if dp:
                texts["[ПРЕПАРАТ/vidal_drug]"] = dp
        if s2.ohlp_result:
            pt = s2.ohlp_result.get("pk_text", "")
            if pt:
                ohlp_tag = "[ПРЕПАРАТ/ohlp]" if s2.ohlp_result.get("level") == "drug" else "[ВЕЩЕСТВО/ohlp]"
                texts[ohlp_tag] = pt
        if s2.edrug3d_result:
            parts = []
            for pn, pv in s2.edrug3d_result.get("params", {}).items():
                parts.append(f"{pn} = {pv.value} {pv.unit}")
            if "cmax_molar" in s2.edrug3d_result:
                parts.append(f"cmax_molar = {s2.edrug3d_result['cmax_molar']} (молярные ед.)")
            if parts:
                texts["[ВЕЩЕСТВО/edrug3d]"] = "\n".join(parts)
        if s2.osp_result:
            parts = []
            for pn, pv in s2.osp_result.get("params", {}).items():
                parts.append(f"{pn} = {pv.value} {pv.unit}")
            if parts:
                texts["[ВЕЩЕСТВО/osp]"] = "\n".join(parts)
        if s2.cvintra_pmc_result:
            cv_parts = []
            cvr = s2.cvintra_pmc_result
            if cvr.get("cvintra_cmax_pct"):
                cv_parts.append(f"CVintra Cmax = {cvr['cvintra_cmax_pct']}%")
            if cvr.get("cvintra_auc_pct"):
                cv_parts.append(f"CVintra AUC = {cvr['cvintra_auc_pct']}%")
            if cvr.get("n_studies"):
                cv_parts.append(f"(из {cvr['n_studies']} BE-исследований, Park et al. 2020)")
            if cvr.get("sample_size_80pwr"):
                cv_parts.append(f"Рекомендуемый размер выборки: {cvr['sample_size_80pwr']} (80% power)")
            if cv_parts:
                texts["[ВЕЩЕСТВО/cvintra_pmc]"] = "\n".join(cv_parts)
        if s2.fda_psg_result:
            cv_thr = s2.fda_psg_result.get("cvintra_threshold")
            if cv_thr:
                texts["[ВЕЩЕСТВО/fda_psg]"] = f"CVintra threshold from FDA PSG: ≥{cv_thr}% (high variability, reference-scaled BE applies)"
        if s2.vidal_mol_result:
            mp = s2.vidal_mol_result.get("pharmacokinetics", "")
            if mp:
                texts["[ВЕЩЕСТВО/vidal_mol]"] = mp
        if s2.drugbank_result:
            db_parts = []
            for fld in ["absorption", "half_life", "volume_of_distribution", "clearance"]:
                txt = s2.drugbank_result.get(fld, "")
                if txt:
                    db_parts.append(f"{fld}: {txt}")
            if db_parts:
                texts["[ВЕЩЕСТВО/drugbank]"] = "\n".join(db_parts)

        if texts:
            st.markdown(f"Источников для анализа: **{len(texts)}**")
            for tag in texts:
                st.markdown(f"- `{tag}` ({len(texts[tag])} симв.)")

            llm_out = llm_extract.extract_pk_from_texts(texts, param_names)
            s2.llm_detail = llm_out

            if llm_out.error:
                st.error(f"Ошибка LLM: {llm_out.error}")
                st_llm.update(label="🤖 LLM: ошибка", state="error")
            else:
                s2.llm_result = llm_out.params
                for pname, pval in s2.llm_result.items():
                    if hasattr(pk, pname):
                        setattr(pk, pname, pval)
                n_found = len(s2.llm_result)
                st.markdown(f"Извлечено параметров: **{n_found}/5**")
                st_llm.update(label=f"🤖 LLM: извлечено {n_found}/5 параметров", state="complete")
        else:
            st.markdown("Нет данных ни из одного источника")
            s2.llm_detail = None
            st_llm.update(label="🤖 LLM: нет входных данных", state="complete")
else:
    if s2.edrug3d_result:
        for pn, pv in s2.edrug3d_result.get("params", {}).items():
            if hasattr(pk, pn):
                setattr(pk, pn, pv)
    if s2.osp_result:
        for pn, pv in s2.osp_result.get("params", {}).items():
            if hasattr(pk, pn) and getattr(pk, pn) is None:
                setattr(pk, pn, pv)
    if s2.cvintra_pmc_result:
        for pn, pv in s2.cvintra_pmc_result.get("params", {}).items():
            if hasattr(pk, pn) and getattr(pk, pn) is None:
                setattr(pk, pn, pv)
    st.info("LLM отключён (нет API ключа). Используются только структурированные числа.")

s2.pk = pk

# LLM details expander
if s2.llm_detail:
    detail = s2.llm_detail
    with st.expander("🔧 Детали LLM (промпт, ответ)", expanded=False):
        if detail.raw_response:
            st.markdown("**JSON ответ LLM:**")
            st.markdown(f'<div class="code-box">{_esc(detail.raw_response)}</div>', unsafe_allow_html=True)
        if detail.user_prompt:
            st.markdown("**Промпт → LLM:**")
            st.markdown(f'<div class="code-box">{_esc(detail.user_prompt)}</div>', unsafe_allow_html=True)
        if detail.system_prompt:
            st.markdown("**Системный промпт:**")
            st.markdown(f'<div class="code-box">{_esc(detail.system_prompt)}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ИТОГОВЫЕ ПАРАМЕТРЫ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="stage-header"><span class="stage-num">∑</span> Итоговые ФК параметры</div>', unsafe_allow_html=True)

for pname, (label, target_unit) in PK_PARAM_LABELS.items():
    val = getattr(pk, pname)
    if val and val.value is not None:
        val_str = f"{val.value:,.2f}" if val.value < 10000 else f"{val.value:,.0f}"
        src_label, src_pill = SOURCE_LABELS.get(val.source, (val.source, "pill-gray"))
        ohlp_is_drug = s2.ohlp_result and s2.ohlp_result.get("level") == "drug" if "ohlp" in val.source else False
        is_drug_level = "drug" in val.source or ohlp_is_drug
        level_icon = "💊" if is_drug_level else "🧬"
        src_url = _get_source_url(val.source, s2)

        extra_lines = ""
        if val.reasoning:
            extra_lines += f'<div style="font-size:0.78rem; color:#475569; margin-top:0.3rem;"><b>LLM:</b> {_esc(val.reasoning)}</div>'
        if val.raw_text:
            extra_lines += f'<div style="font-size:0.72rem; color:#94a3b8; margin-top:0.15rem; font-style:italic;"><b>Цитата:</b> «{_esc(val.raw_text)}»</div>'
        if src_url:
            extra_lines += f'<div style="font-size:0.72rem; margin-top:0.15rem;"><a href="{src_url}" target="_blank" style="color:#2563eb;">↗ Проверить в источнике</a></div>'

        st.markdown(f"""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
            padding:0.8rem 1rem; margin:0.4rem 0; border-left:4px solid {'#059669' if is_drug_level else '#7c3aed'};">
            <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
                <strong style="font-size:1rem; min-width:70px;">{label}</strong>
                <span style="font-size:1.2rem; font-weight:800; color:{'#059669' if is_drug_level else '#7c3aed'};">{val_str} {val.unit}</span>
                <span class="pill {src_pill}">{level_icon} {src_label}</span>
            </div>
            {extra_lines}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
            padding:0.8rem 1rem; margin:0.4rem 0; border-left:4px solid #cbd5e1;">
            <div style="display:flex; align-items:center; gap:0.6rem;">
                <strong style="font-size:1rem; min-width:70px;">{label}</strong>
                <span style="font-size:1.2rem; font-weight:800; color:#cbd5e1;">—</span>
                <span style="color:#94a3b8; font-size:0.8rem;">{target_unit}</span>
                <span class="pill pill-gray">не найдено</span>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Metrics ──
filled = pk.filled_params()
total = len(PK_PARAM_LABELS)

mcols = st.columns(3)
with mcols[0]:
    color = "#059669" if len(filled) >= 4 else "#f59e0b" if len(filled) >= 2 else "#ef4444"
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{len(filled)}/{total}</div>'
                f'<div class="metric-label">параметров</div></div>', unsafe_allow_html=True)
with mcols[1]:
    if pk.t_half_h and pk.t_half_h.value:
        washout = math.ceil(5 * pk.t_half_h.value / 24)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{washout}+ дн</div>'
                    f'<div class="metric-label">отмывочный (5×T½)</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-card"><div class="metric-value pk-miss">—</div>'
                    f'<div class="metric-label">отмывочный период</div></div>', unsafe_allow_html=True)
with mcols[2]:
    if pk.tmax_h and pk.tmax_h.value:
        st.markdown(f'<div class="metric-card"><div class="metric-value">&lt;{2 * pk.tmax_h.value:.1f} ч</div>'
                    f'<div class="metric-label">рвота (2×Tmax)</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-card"><div class="metric-value pk-miss">—</div>'
                    f'<div class="metric-label">критерий рвоты</div></div>', unsafe_allow_html=True)

# ── Full log ──
with st.expander("🔧 Полный лог", expanded=False):
    for line in s2.log:
        st.markdown(f'<span style="font-family:monospace; font-size:0.78rem; color:#475569;">{_esc(line)}</span>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СТАДИЯ 3 — ГЕНЕРАЦИЯ СИНОПСИСА
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="stage-header"><span class="stage-num">3</span> Генерация синопсиса протокола</div>', unsafe_allow_html=True)

from pipeline.stage3 import Stage3Input, generate_synopsis, generate_docx

ref_drug_name = drug.trade_names.split(",")[0].strip() if drug and drug.trade_names else ""
fda_strength = ""
fda_form = ""
if s2.fda_psg_result:
    fda_strength = s2.fda_psg_result.get("strength", "") or ""
    fda_form = s2.fda_psg_result.get("dosage_form", "") or ""
vidal_form = ""
if s2.vidal_drug_result:
    vidal_form = s2.vidal_drug_result.get("form_details", "") or ""

default_test_name = f"{inn_ru.capitalize()}-Тест" if inn_ru else ""
default_form = fda_form or drug.dosage_form or (vidal_form[:80] if vidal_form else "")

with st.form("stage3_form"):
    st.markdown("**Параметры для синопсиса**")

    col_a, col_b = st.columns(2)
    with col_a:
        s3_test_drug = st.text_input("Исследуемый препарат (генерик)", value=default_test_name)
        s3_dosage_form = st.text_input("Лекарственная форма", value=default_form)
        s3_strength = st.text_input("Дозировка", value=fda_strength, placeholder="например: 400 мг")
        s3_sponsor = st.text_input("Спонсор исследования", value="", placeholder="ХХХХХ, Россия")
    with col_b:
        s3_fasting_fed = st.selectbox(
            "Режим приёма", ["", "fasting", "fed", "both"],
            format_func=lambda x: {"": "Авто (из данных)", "fasting": "Натощак",
                                    "fed": "После еды", "both": "Оба"}.get(x, x),
        )
        s3_design = st.selectbox(
            "Дизайн исследования", ["", "2x2", "replicated", "parallel"],
            format_func=lambda x: {"": "Авто (по CVintra)", "2x2": "2×2 перекрёстный",
                                    "replicated": "Реплицированный", "parallel": "Параллельный"}.get(x, x),
        )
        s3_study_phases = st.selectbox(
            "Кратность дозы", ["single", "multiple"],
            format_func=lambda x: {"single": "Однократная", "multiple": "Многократная"}.get(x, x),
        )
        s3_gender = st.selectbox(
            "Пол добровольцев", ["both", "male", "female"],
            format_func=lambda x: {"both": "Мужчины и женщины", "male": "Только мужчины",
                                    "female": "Только женщины"}.get(x, x),
        )

    st.markdown("**Дополнительные параметры**")
    col_c, col_d = st.columns(2)
    with col_c:
        s3_cv_user = st.number_input("CVintra (%) — если известен, 0 = авто", min_value=0.0, max_value=200.0, value=0.0, step=1.0)
        s3_age_range = st.text_input("Возрастной диапазон", value="18-45", placeholder="18-45")
    with col_d:
        s3_rsabe = st.checkbox("Использовать RSABE (для Cmax)")
        s3_additional = st.text_area("Дополнительные требования", value="", placeholder="Свободный текст...", height=80)

    s3_submit = st.form_submit_button("📋 Сгенерировать синопсис", use_container_width=True)

if s3_submit:
  try:
    s3_input = Stage3Input(
        drug_info=drug,
        s2=s2,
        test_drug_name=s3_test_drug or default_test_name or "Исследуемый препарат",
        sponsor=s3_sponsor,
        dosage_form=s3_dosage_form,
        strength=s3_strength,
        fasting_fed=s3_fasting_fed,
        cv_intra_user=s3_cv_user,
        use_rsabe=s3_rsabe,
        design_preference=s3_design,
        study_phases=s3_study_phases,
        gender=s3_gender,
        age_range=s3_age_range,
        additional_requirements=s3_additional,
    )

    def _call_llm_stage3(prompt: str) -> str:
        from pipeline.config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
        if not DEEPSEEK_API_KEY:
            return "{}"
        from openai import OpenAI
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "Ты эксперт по клиническим исследованиям биоэквивалентности. Отвечай валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=8000,
        )
        return resp.choices[0].message.content or "{}"

    # ── Шаг 3.1: Расчёт дизайна ──
    with st.status("🔬 Шаг 3.1 — Определение дизайна исследования...", expanded=True) as st_s31:
        from pipeline.stage3 import compute_derived
        computed = compute_derived(s3_input)
        design = computed.get("design", {})

        st.markdown(f"""
| Параметр | Значение |
|---|---|
| **Дизайн** | {design.get('design', '—')} |
| **Границы БЭ** | {design.get('be_limits', '—')} |
| **NTI** | {'да' if computed.get('is_nti') else 'нет'} |
| **HVD** | {'да' if computed.get('is_hvd') else 'нет'} |
| **CVintra** | {f"{computed['cv_intra']:.1f}%" if computed.get('cv_intra') else '—'} |
| **T½** | {f"{computed['t_half']} ч" if computed.get('t_half') else '—'} |
| **Tmax** | {f"{computed['tmax']} ч" if computed.get('tmax') else '—'} |
| **Приём** | {computed.get('fasting_or_fed', '—')} |
""")
        st.info(design.get("rationale", ""))
        st_s31.update(label=f"✅ Дизайн: {design.get('design', '?')} — {design.get('be_limits', '')}", state="complete")

    # ── Шаг 3.2: Расчёт выборки ──
    sample = computed.get("sample_size")
    n_to_screen = computed.get("n_to_screen")
    with st.status("🧮 Шаг 3.2 — Расчёт размера выборки...", expanded=True) as st_s32:
        if sample:
            st.code(sample["formula_note"])
            st_s32.update(label=f"✅ Выборка: {sample['n_total']} доб. ({sample['n_per_group']} на гр.) | скринировать до {n_to_screen or '—'}", state="complete")
        else:
            st.warning("CVintra не определён — размер выборки не рассчитан. Минимум по Правилу 85: 12 добровольцев.")
            st_s32.update(label="⚠️ Выборка: CVintra не найден (мин. 12)", state="complete")

    # ── Шаг 3.3: График крови ──
    tp = computed.get("timepoints")
    with st.status("🩸 Шаг 3.3 — График отбора крови...", expanded=True) as st_s33:
        if tp:
            st.code(tp["schedule_text"])
            st.markdown(f"""
| | |
|---|---|
| Точек | **{tp['n_samples']}** |
| Период отбора | **{tp['end_time_h']:.0f} ч** |
| Кровь за 1 период | **{tp['total_blood_per_period_ml']:.0f} мл** |
| Кровь за 2 периода | **{tp['total_blood_2periods_ml']:.0f} мл** |
""")
            st.caption(tp["rationale"])
            st_s33.update(label=f"✅ График крови: {tp['n_samples']} точек до {tp['end_time_h']:.0f} ч", state="complete")
        else:
            st.warning("Tmax или T½ не определены — график не рассчитан.")
            st_s33.update(label="⚠️ График крови: нет данных", state="complete")

    # ── Шаг 3.4: Отмывочный и рвота ──
    with st.status("⏱️ Шаг 3.4 — Отмывочный период и критерий рвоты...", expanded=True) as st_s34:
        washout = computed.get("washout_days")
        vomit = computed.get("vomit_criterion_h")
        if washout or vomit:
            parts = []
            if washout:
                parts.append(f"**Отмывочный период:** ≥ {washout} дней (⌈5 × T½ / 24⌉)")
            if vomit:
                parts.append(f"**Критерий рвоты:** < {vomit} ч после приёма (2 × Tmax)")
            st.markdown("\n\n".join(parts))
            st_s34.update(label=f"✅ Отмывочный: {washout or '—'} дн | Рвота: <{vomit or '—'} ч", state="complete")
        else:
            st.warning("T½ и Tmax не определены.")
            st_s34.update(label="⚠️ Отмывочный/рвота: нет данных", state="complete")

    # ── Шаг 3.5: Сбор данных для LLM ──
    from pipeline.stage3 import collect_all_data, generate_synopsis_step, LLM_CALLS, _load_rule85, _collect_source_links, generate_programmatic_fields
    with st.status("📚 Шаг 3.5 — Сбор данных из всех источников...", expanded=True) as st_s35:
        all_data = collect_all_data(s3_input)
        src_names = list(all_data.keys())
        st.markdown(f"Собрано {_plural(len(src_names), 'блок', 'блока', 'блоков')} данных для генерации синопсиса:")

        _S3_SOURCE_GROUPS = {
            "📄 ОХЛП": {
                "ohlp_pk_text": "5.2 Фармакокинетика", "ohlp_pd_text": "5.1 Фармакодинамика",
                "ohlp_contra_text": "4.3 Противопоказания", "ohlp_adverse_text": "4.8 Нежелательные реакции",
                "ohlp_dosing_text": "4.2 Дозирование", "ohlp_interactions_text": "4.5 Взаимодействия",
                "ohlp_indications_text": "4.1 Показания", "ohlp_precautions_text": "4.4 Особые указания",
                "ohlp_pregnancy_text": "4.6 Беременность/лактация", "ohlp_overdose_text": "4.9 Передозировка",
                "ohlp_composition_text": "2. Состав", "ohlp_form_text": "3. Лекарственная форма",
                "ohlp_excipients_text": "6.1 Вспомогательные вещества",
                "ohlp_shelf_life_text": "6.3 Срок годности", "ohlp_storage_text": "6.4 Хранение",
            },
            "🏷️ Видаль (препарат)": {"vidal_drug": "ФК + состав"},
            "🧬 Видаль (вещество)": {
                "vidal_mol_pharmacokinetics": "Фармакокинетика",
                "vidal_mol_pharmacology": "Фармакология",
                "vidal_mol_indications": "Показания",
                "vidal_mol_contraindications": "Противопоказания",
            },
            "💊 DrugBank": {
                "drugbank_absorption": "Absorption", "drugbank_half_life": "Half-life",
                "drugbank_protein_binding": "Protein binding",
                "drugbank_volume_of_distribution": "Vd", "drugbank_clearance": "Clearance",
                "drugbank_metabolism": "Metabolism", "drugbank_route_of_elimination": "Elimination",
            },
            "🇺🇸 FDA PSG": {
                "fda_psg_design_fasting": "Дизайн (натощак)", "fda_psg_design_fed": "Дизайн (с едой)",
                "fda_psg_strength": "Дозировка", "fda_psg_subjects": "Субъекты",
                "fda_psg_analytes": "Аналиты", "fda_psg_be_based_on": "BE based on",
                "fda_psg_waiver": "Waiver", "fda_psg_additional_comments": "Доп. комментарии",
                "fda_psg_dissolution_info": "Тест растворения",
            },
        }
        for group_label, keys_map in _S3_SOURCE_GROUPS.items():
            found_keys = {k: v for k, v in keys_map.items() if k in all_data}
            if not found_keys:
                continue
            st.markdown(f"**{group_label}** — {_plural(len(found_keys), 'блок', 'блока', 'блоков')}:")
            for data_key, nice_name in found_keys.items():
                txt = all_data[data_key]
                with st.expander(f"{nice_name} ({len(txt)} симв.)", expanded=False):
                    st.markdown(f'<div class="text-block">{_esc(txt)}</div>', unsafe_allow_html=True)

        st_s35.update(label=f"✅ Собрано {_plural(len(src_names), 'блок', 'блока', 'блоков')} данных", state="complete")

    # ── Шаг 3.6: Программные поля (шаблоны из instructions.docx) ──
    with st.status("📝 Шаг 3.6 — Генерация программных полей...", expanded=True) as st_s36:
        synopsis = generate_programmatic_fields(s3_input, computed)
        prog_count = len([v for v in synopsis.values() if v])
        st.markdown(f"Сгенерировано **{prog_count}** полей программно (шаблоны + формулы)")
        st_s36.update(label=f"✅ {prog_count} полей сгенерировано программно", state="complete")

    # ── Шаги 3.7.x: LLM-вызовы (3: дизайн, критерии, безопасность) ──
    from pipeline.config import DEEPSEEK_API_KEY
    llm_fn = _call_llm_stage3 if DEEPSEEK_API_KEY else None
    rule85 = _load_rule85()

    llm_calls_log = []
    total_llm_fields = 0

    if llm_fn:
        for i, call_def in enumerate(LLM_CALLS, 1):
            step_label = f"🤖 Шаг 3.7.{i} — {call_def['name']}"
            with st.status(f"{step_label}...", expanded=True) as st_llm_step:
                st.markdown(f"**Секции:** {', '.join(call_def['fields'])}")
                relevant_keys = [k for k in call_def["data_keys"] if k in all_data]
                if relevant_keys:
                    st.markdown(f"**Данные →** {', '.join(relevant_keys)}")
                else:
                    st.markdown("**Данные →** общий контекст + Правило 85")
                try:
                    result = generate_synopsis_step(call_def, s3_input, computed, all_data, rule85, llm_fn)
                    synopsis.update(result["data"])
                    llm_calls_log.append(result)
                    received = result["fields_received"]
                    total_llm_fields += len(received)
                    st.markdown(f"✓ Получено {_plural(len(received), 'секция', 'секции', 'секций')}: {', '.join(received)}")
                    st_llm_step.update(label=f"✅ {call_def['name']}: {_plural(len(received), 'секция', 'секции', 'секций')}", state="complete")
                except Exception as e:
                    st.error(f"Ошибка: {e}")
                    llm_calls_log.append({"call_id": call_def["id"], "error": str(e)})
                    st_llm_step.update(label=f"❌ {call_def['name']}: ошибка", state="error")
    else:
        st.warning("API ключ не задан — критерии и описания препаратов не сгенерированы, только расчёты и шаблоны.")

    # Собираем итоговый результат
    from pipeline.stage3 import Stage3Result
    sources_used = []
    _collect_source_links(s2, sources_used)
    s3_result = Stage3Result(
        synopsis=synopsis,
        computed=computed,
        sources_used=sources_used,
        llm_calls_log=llm_calls_log,
    )

    # ── Шаг 3.8: Генерация Word ──
    with st.status("📄 Шаг 3.8 — Генерация Word-документа...", expanded=True) as st_s38:
        docx_bytes = generate_docx(s3_result)
        st.markdown(f"Документ: **{len(docx_bytes) / 1024:.1f} КБ** | {prog_count} программных + {total_llm_fields} LLM полей")
        st_s38.update(label=f"✅ Word: {len(docx_bytes) / 1024:.1f} КБ", state="complete")

    # ── Предпросмотр синопсиса ──
    st.markdown("---")
    st.markdown("### 📝 Предпросмотр синопсиса")
    syn = s3_result.synopsis
    preview_fields = [
        ("Название протокола", "protocol_title"),
        ("Идентификационный номер", "protocol_id"),
        ("Цель исследования", "study_objectives"),
        ("Задачи", "tasks"),
        ("Дизайн исследования", "study_design"),
        ("Методология", "methodology"),
        ("Количество добровольцев", "sample_size_text"),
        ("Критерии включения", "inclusion_criteria"),
        ("Критерии невключения", "exclusion_criteria"),
        ("Критерии исключения", "withdrawal_criteria"),
        ("Исследуемый препарат (T)", "test_drug_details"),
        ("Референтный препарат (R)", "reference_drug_details"),
        ("Периоды исследования", "study_periods"),
        ("Продолжительность", "study_duration"),
        ("ФК параметры", "pk_parameters"),
        ("Аналитический метод", "analytical_method"),
        ("Критерии БЭ", "be_criteria"),
        ("Безопасность", "safety_analysis"),
        ("Расчёт выборки", "sample_size_calculation"),
        ("Статистические методы", "statistical_methods"),
        ("Рандомизация", "blinding_randomization"),
        ("Этика", "ethical_aspects"),
        ("Версия протокола", "protocol_version"),
    ]
    for label, key in preview_fields:
        val = syn.get(key, "")
        if val:
            with st.expander(f"**{label}**", expanded=False):
                st.markdown(val[:2000])

    # ── Источники ──
    if s3_result.sources_used:
        st.markdown("### 🔗 Источники данных")
        for src in s3_result.sources_used:
            url = src.get("url", "")
            if url.startswith("http"):
                st.markdown(f"- [{src['name']}]({url})")
            else:
                st.markdown(f"- {src['name']}: {url}")

    # ── Кнопка скачивания — в самом конце ──
    st.markdown("---")
    st.markdown("### 📥 Скачать синопсис")
    st.download_button(
        label="📥 Скачать синопсис (Word .docx)",
        data=docx_bytes,
        file_name=f"synopsis_{(drug.matched_inn if drug else 'drug').replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
  except Exception as _e3:
    import traceback as _tb3
    _err_text = _tb3.format_exc()
    st.error(f"Ошибка Stage 3: {_e3}")
    st.code(_err_text, language="python")
    import logging; logging.getLogger("streamlit").error("STAGE3 ERROR: %s", _err_text)
