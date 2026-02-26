"""
Расчёт размера выборки для исследования биоэквивалентности.

Метод: Power approach for Two One-Sided Tests (TOST).
Основан на Правилах ЕАЭС (Решение №85), п. 26, 81, 85, 87.

Границы БЭ: 80.00–125.00% (стандартные)
             90.00–111.11% (NTI)

Формула (нормальное приближение, логшкала):
  n_per_group = ((z_{1-α} + z_{1-β})² × 2 × σ²_w) / δ²

Где:
  σ²_w = ln(1 + CV²)   — within-subject variance в логшкале
  δ = ln(θ) — допустимое отклонение (θ = 1.25 → δ = ln(1.25))
  α = 0.05 (для 90% CI)
  β = 1 - power

Ссылки:
  - Diletti et al. (1991) Int J Clin Pharmacol Ther Toxicol
  - Chow & Liu (2009) Design and Analysis of Bioavailability and Bioequivalence Studies
  - Решение Совета ЕАЭК от 03.11.2016 N 85, раздел III
"""

import math
from typing import Optional, Dict, Any

# scipy доступна для точного расчёта через нецентральное t-распределение
try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def calc_sample_size(
    cv_intra_pct: float,
    power: float = 0.80,
    alpha: float = 0.05,
    theta: float = 1.25,
    design: str = "2x2",
    dropout_pct: float = 15.0,
) -> Dict[str, Any]:
    """
    Расчёт размера выборки для BE-исследования.

    Args:
        cv_intra_pct: CVintra в процентах (например 25.0 для 25%)
        power: мощность (0.80 или 0.90)
        alpha: уровень значимости (0.05 для 90% CI)
        theta: верхняя граница БЭ (1.25 стандартно, 1.1111 для NTI)
        design: "2x2" (стандартный crossover) или "replicated"
        dropout_pct: % запаса на выбывание

    Returns:
        dict с полями:
            n_per_group: кол-во на группу
            n_total: общее (с запасом на dropout)
            n_evaluable: минимум для анализа
            cv_used: использованный CV%
            power_used: мощность
            design_used: дизайн
            is_nti: True если суженные границы
            formula_note: текстовое описание
    """
    cv = cv_intra_pct / 100.0
    sigma_w2 = math.log(1 + cv ** 2)
    delta = math.log(theta)

    if HAS_SCIPY:
        n_eval = _calc_scipy(sigma_w2, delta, alpha, power)
    else:
        n_eval = _calc_normal_approx(sigma_w2, delta, alpha, power)

    n_eval = max(n_eval, 12)

    if design == "replicated":
        n_eval_adj = math.ceil(n_eval * 0.75)
        n_eval_adj = max(n_eval_adj, 12)
    else:
        n_eval_adj = n_eval

    n_total = math.ceil(n_eval_adj / (1 - dropout_pct / 100.0))
    if n_total % 2 != 0:
        n_total += 1

    screen_fail_pct = 20.0
    n_to_screen = math.ceil(n_total / (1 - screen_fail_pct / 100.0))
    if n_to_screen % 2 != 0:
        n_to_screen += 1

    is_nti = abs(theta - 1.1111) < 0.01

    return {
        "n_per_group": n_total // 2,
        "n_total": n_total,
        "n_evaluable": n_eval_adj,
        "n_to_screen": n_to_screen,
        "cv_used": cv_intra_pct,
        "power_used": power,
        "alpha_used": alpha,
        "theta_used": theta,
        "design_used": design,
        "is_nti": is_nti,
        "dropout_pct": dropout_pct,
        "screen_fail_pct": screen_fail_pct,
        "method": "scipy_nct" if HAS_SCIPY else "normal_approx",
        "formula_note": _make_note(cv_intra_pct, power, theta, design, n_eval_adj, n_total, n_to_screen, is_nti),
    }


def _calc_normal_approx(sigma_w2: float, delta: float, alpha: float, power: float) -> int:
    """Нормальное приближение (Diletti et al.)."""
    from math import ceil
    z_a = _z(1 - alpha)
    z_b = _z(power)
    n = ceil((z_a + z_b) ** 2 * 2 * sigma_w2 / delta ** 2)
    return n


def _calc_scipy(sigma_w2: float, delta: float, alpha: float, power: float) -> int:
    """Точный расчёт через нецентральное t-распределение."""
    from math import ceil, sqrt

    for n in range(6, 1000):
        df = n - 2  # для 2x2 crossover: df = n - 2
        se = sqrt(2 * sigma_w2 / n)
        nc = delta / se
        t_crit = sp_stats.t.ppf(1 - alpha, df)
        pwr = 1 - sp_stats.nct.cdf(t_crit, df, nc) + sp_stats.nct.cdf(-t_crit, df, nc)
        if pwr >= power:
            return n
    return 1000


def _z(p: float) -> float:
    """Квантиль стандартного нормального."""
    if HAS_SCIPY:
        return sp_stats.norm.ppf(p)
    # Приближение Abramowitz & Stegun
    if p <= 0 or p >= 1:
        return 0.0
    if p < 0.5:
        return -_z(1 - p)
    t = math.sqrt(-2 * math.log(1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t ** 2) / (1 + d1 * t + d2 * t ** 2 + d3 * t ** 3)


def _make_note(cv: float, power: float, theta: float, design: str, n_eval: int, n_total: int, n_to_screen: int, is_nti: bool) -> str:
    bounds = "90.00–111.11%" if is_nti else "80.00–125.00%"
    design_ru = "реплицированный перекрёстный" if design == "replicated" else "двухпериодный перекрёстный (2×2)"
    if design == "parallel":
        design_ru = "параллельный"
    return (
        f"CVintra = {cv:.1f}%, мощность = {power*100:.0f}%, α = 0.05\n"
        f"Границы БЭ: {bounds} (90% ДИ)\n"
        f"Дизайн: {design_ru}\n"
        f"Минимум для анализа: {n_eval} добровольцев\n"
        f"С учётом выбывания (15%): {n_total} добровольцев ({n_total // 2} на группу)\n"
        f"С учётом скрин-фейла (20%): скринировать до {n_to_screen} добровольцев\n"
        f"Основание: Решение Совета ЕАЭК от 03.11.2016 N 85, п. 26, 81, 87"
    )


def determine_design(
    cv_intra_pct: Optional[float],
    is_hvd: bool = False,
    is_nti: bool = False,
    is_replicated_fda: bool = False,
) -> Dict[str, Any]:
    """
    Определить дизайн исследования на основе данных.

    Returns:
        dict: design, theta, be_limits, rationale
    """
    if is_nti:
        return {
            "design": "2x2",
            "theta": 1.1111,
            "be_limits": "90.00–111.11%",
            "rationale": (
                "Препарат с узким терапевтическим индексом (NTI). "
                "Границы БЭ сужены до 90.00–111.11% (Решение №85, п. 85). "
                "Стандартный двухпериодный перекрёстный дизайн."
            ),
        }

    need_replicated = is_replicated_fda or is_hvd or (cv_intra_pct is not None and cv_intra_pct >= 30)

    if need_replicated:
        return {
            "design": "replicated",
            "theta": 1.25,
            "be_limits": "80.00–125.00% (расширение Cmax допускается при обосновании)",
            "rationale": (
                f"Высокая внутрисубъектная вариабельность (CVintra {'≥ 30%' if cv_intra_pct and cv_intra_pct >= 30 else '— HVD по FDA'}). "
                "Рекомендуется реплицированный перекрёстный дизайн (Решение №85, п. 16, подраздел 11). "
                "Для Cmax допускается расширение границ при соответствующем обосновании."
            ),
        }

    return {
        "design": "2x2",
        "theta": 1.25,
        "be_limits": "80.00–125.00%",
        "rationale": (
            "Стандартный двухпериодный перекрёстный дизайн (2×2) "
            "с однократным приёмом (Решение №85, п. 15). "
            "Границы БЭ: 80.00–125.00% (90% ДИ) для AUC₀₋ₜ и Cmax."
        ),
    }
