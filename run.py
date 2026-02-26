#!/usr/bin/env python3
"""
Точка входа: МНН → оригинальный препарат → ФК параметры.
Стадии 1 и 2.
"""

import argparse
import sys

from pipeline.stage1 import find_original, find_all_by_inn
from pipeline.stage2 import find_pk_params
from pipeline.models import PK_PARAM_LABELS


def print_header(title: str):
    width = 70
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_stage1(inn: str):
    print_header(f"СТАДИЯ 1: МНН → оригинальный препарат")
    print(f"  Запрос: {inn}")
    print()

    all_matches = find_all_by_inn(inn)

    if not all_matches:
        print(f"  Ничего не найдено в реестре ЕАЭС.")
        return None

    print(f"  Найдено в реестре: {len(all_matches)} записей")
    print(f"  {'Тип':<25} {'Торговые наименования':<40} {'Совпадение'}")
    print(f"  {'-'*25} {'-'*40} {'-'*15}")

    for d in all_matches:
        names_short = d.trade_names[:37] + "..." if len(d.trade_names) > 40 else d.trade_names
        match_info = f"{d.match_type} ({d.match_score:.0f}%)" if d.match_type == "fuzzy" else d.match_type
        marker = " *" if d.drug_kind == "оригинальный" else ""
        form_short = (d.dosage_form[:30] + "…") if len(d.dosage_form) > 30 else d.dosage_form
        print(f"  {d.drug_kind:<25} {names_short:<40} {form_short:<35} {match_info}{marker}")

    original = None
    originals = [d for d in all_matches if d.drug_kind == "оригинальный"]
    if originals:
        original = originals[0]
        print(f"\n  >> Оригинальный препарат: {original.trade_names}")
        print(f"     МНН: {original.matched_inn}")
        print(f"     АТХ: {original.atc_code}")
        print(f"     Держатель РУ: {original.holders}")
    else:
        original = all_matches[0]
        print(f"\n  >> Оригинальный не найден, используем: {original.trade_names} ({original.drug_kind})")

    return original


def print_stage2(drug, use_llm: bool = True):
    print_header(f"СТАДИЯ 2: препарат → ФК параметры")
    print(f"  Препарат: {drug.trade_names}")
    print(f"  МНН: {drug.matched_inn}")
    print()

    result = find_pk_params(drug, use_llm=use_llm)

    for line in result.log:
        print(f"  {line}")

    print()
    print(f"  {'=' * 60}")
    print(f"  ИТОГОВЫЕ ФК ПАРАМЕТРЫ")
    print(f"  {'=' * 60}")
    print(f"  {'Параметр':<20} {'Значение':>12} {'Единица':>12} {'Источник':<15}")
    print(f"  {'-' * 60}")

    pk = result.pk
    for pname, (label, target_unit) in PK_PARAM_LABELS.items():
        val = getattr(pk, pname)
        if val and val.value is not None:
            print(f"  {label:<20} {val.value:>12.2f} {val.unit:>12} {val.source:<15}")
        else:
            print(f"  {label:<20} {'—':>12} {target_unit:>12} {'':>15}")

    filled = pk.filled_params()
    missing = pk.missing_params()
    print(f"  {'-' * 60}")
    print(f"  Найдено: {len(filled)}/5")
    if missing:
        print(f"  Не найдены: {', '.join(missing)}")

    return result


def main():
    parser = argparse.ArgumentParser(description="МНН → оригинальный препарат → ФК параметры")
    parser.add_argument("--inn", type=str, help="МНН для поиска")
    parser.add_argument("--no-llm", action="store_true", help="Не использовать DeepSeek LLM")
    args = parser.parse_args()

    if not args.inn:
        examples = ["амлодипин", "вилдаглиптин", "метформин", "ибупрофен", "омепразол"]
        print("Демо-режим. Примеры:")
        for ex in examples:
            print(f"  python run.py --inn \"{ex}\"")
        print()
        args.inn = "ибупрофен"
        print(f"Запускаю с '{args.inn}'...")

    drug = print_stage1(args.inn)
    if drug:
        print_stage2(drug, use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
