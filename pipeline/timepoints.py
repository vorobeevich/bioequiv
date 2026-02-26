"""
Генерация графика отбора образцов крови для исследования БЭ.

Основано на: Решение ЕАЭК №85, п. 38, 47.
- Достаточное количество точек вокруг Tmax для точной оценки Cmax
- Cmax не должна быть первой точкой на кривой
- AUC(0-t) ≥ 80% от AUC(0-∞)
- Отбор не более 72 ч (п. 38)
- Не менее 3-4 точек в терминальной фазе
"""

import math
from typing import List, Dict, Any, Optional


def generate_timepoints(
    tmax_h: float,
    t_half_h: float,
    max_duration_h: float = 72.0,
) -> Dict[str, Any]:
    """
    Генерация оптимального графика отбора крови.

    Args:
        tmax_h: Tmax в часах
        t_half_h: T½ в часах
        max_duration_h: макс. продолжительность отбора (≤72 ч по Правилу 85)

    Returns:
        dict: timepoints_h, n_samples, total_blood_ml, schedule_text, rationale
    """
    max_duration_h = min(max_duration_h, 72.0)

    end_time = min(max(5 * t_half_h, 3 * tmax_h, 24.0), max_duration_h)

    points = set()

    points.add(0.0)

    pre_tmax = _pre_tmax_points(tmax_h)
    points.update(pre_tmax)

    around_tmax = _around_tmax_points(tmax_h)
    points.update(around_tmax)

    post_peak = _post_peak_points(tmax_h, t_half_h, end_time)
    points.update(post_peak)

    terminal = _terminal_points(t_half_h, end_time)
    points.update(terminal)

    points = {p for p in points if p <= end_time + 0.01}

    timepoints = sorted(points)

    blood_per_sample_ml = 5.0
    dead_volume_ml = 0.5
    n_samples = len(timepoints)
    total_blood_ml = n_samples * (blood_per_sample_ml + dead_volume_ml)
    total_blood_2periods_ml = total_blood_ml * 2

    schedule_text = _format_schedule(timepoints)

    return {
        "timepoints_h": timepoints,
        "n_samples": n_samples,
        "end_time_h": end_time,
        "blood_per_sample_ml": blood_per_sample_ml,
        "total_blood_per_period_ml": total_blood_ml,
        "total_blood_2periods_ml": total_blood_2periods_ml,
        "schedule_text": schedule_text,
        "rationale": _make_rationale(tmax_h, t_half_h, n_samples, end_time),
    }


def _pre_tmax_points(tmax_h: float) -> List[float]:
    """Точки до Tmax — густо, для захвата фазы абсорбции."""
    pts = []
    if tmax_h <= 1.0:
        for m in [5, 10, 15, 20, 30, 45]:
            t = m / 60.0
            if t < tmax_h * 0.9:
                pts.append(round(t, 4))
    elif tmax_h <= 3.0:
        for m in [15, 30, 45]:
            t = m / 60.0
            if t < tmax_h * 0.9:
                pts.append(round(t, 4))
        for h in [1.0, 1.5, 2.0]:
            if h < tmax_h * 0.9:
                pts.append(h)
    else:
        for h in [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]:
            if h < tmax_h * 0.9:
                pts.append(h)
    return pts


def _around_tmax_points(tmax_h: float) -> List[float]:
    """Точки вокруг Tmax — самые плотные."""
    pts = []
    if tmax_h <= 1.0:
        step = 0.25
    elif tmax_h <= 4.0:
        step = 0.5
    else:
        step = 1.0

    for offset in [-2 * step, -step, 0, step, 2 * step]:
        t = tmax_h + offset
        if t > 0:
            pts.append(round(t, 4))
    return pts


def _post_peak_points(tmax_h: float, t_half_h: float, end_time: float) -> List[float]:
    """Точки после пика — постепенно разреживаются."""
    pts = []
    start = tmax_h * 1.5
    if start < tmax_h + 1:
        start = tmax_h + 1

    if t_half_h <= 4:
        steps = [1, 2, 3, 4, 6, 8]
    elif t_half_h <= 12:
        steps = [2, 4, 6, 8, 10, 12]
    else:
        steps = [2, 4, 8, 12, 16, 24]

    for s in steps:
        t = tmax_h + s
        if start <= t <= end_time:
            pts.append(round(t, 2))

    return pts


def _terminal_points(t_half_h: float, end_time: float) -> List[float]:
    """Точки в терминальной фазе (≥3-4 точки, п.38)."""
    pts = []
    if end_time <= 24:
        candidates = [12, 16, 20, 24]
    elif end_time <= 48:
        candidates = [12, 16, 24, 36, 48]
    else:
        candidates = [12, 16, 24, 36, 48, 60, 72]

    for t in candidates:
        if t <= end_time:
            pts.append(float(t))

    return pts


def _format_schedule(timepoints: List[float]) -> str:
    """Человекочитаемый формат графика."""
    parts = []
    for t in timepoints:
        if t == 0:
            parts.append("0 (до приёма)")
        elif t < 1:
            parts.append(f"{t*60:.0f} мин")
        elif t == int(t):
            parts.append(f"{int(t)} ч")
        else:
            parts.append(f"{t:.2g} ч")
    return ", ".join(parts)


def _make_rationale(tmax_h: float, t_half_h: float, n_samples: int, end_time: float) -> str:
    return (
        f"График отбора: {n_samples} точек в течение {end_time:.0f} ч.\n"
        f"Tmax ≈ {tmax_h} ч → плотный отбор в первые {tmax_h*2:.1f} ч для точной оценки Cmax.\n"
        f"T½ ≈ {t_half_h} ч → отбор до {end_time:.0f} ч обеспечивает AUC(0-t) ≥ 80% от AUC(0-∞).\n"
        f"Терминальная фаза: ≥3 точки для оценки kel.\n"
        f"Основание: Решение ЕАЭК №85, п. 38, 47."
    )
