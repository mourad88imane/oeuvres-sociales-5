"""
============================================================
AI MATH UTILITIES — Fonctions statistiques avancées
============================================================
Pure Python / numpy-ready pour calculs ML.
Toutes les méthodes gèrent les cas aux limites.
"""
import math
from statistics import mean, stdev
from typing import Optional


def linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Moindres carrés ordinaires → (pente, intercept, r²)."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0), 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den if den else 0.0
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot else 0.0
    return slope, intercept, r2


def zscore_anomalies(values: list[float], threshold: float = 2.0) -> list[tuple[int, float, float]]:
    """Index, valeur et z-score des points au-delà du seuil."""
    if len(values) < 3:
        return []
    m = mean(values)
    s = stdev(values)
    if s == 0:
        return []
    return [(i, v, (v - m) / s) for i, v in enumerate(values) if abs((v - m) / s) > threshold]


def iqr_anomalies(values: list[float], multiplier: float = 1.5) -> list[tuple[int, float]]:
    """Détection par intervalle interquartile (robuste aux outliers)."""
    if len(values) < 4:
        return []
    s = sorted(values)
    n = len(s)
    q1 = s[n // 4]
    q3 = s[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return [(i, v) for i, v in enumerate(values) if v < lower or v > upper]


def moving_average(values: list[float], window: int = 3) -> list[float]:
    """Moyenne mobile simple."""
    if len(values) < window:
        return values[:]
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start:i + 1]
        result.append(mean(chunk))
    return result


def moving_average_anomalies(
    values: list[float],
    window: int = 3,
    std_multiplier: float = 2.0,
) -> list[tuple[int, float, float, float]]:
    """Anomalies basées sur l'écart à la moyenne mobile : (idx, valeur, attendu, écart)."""
    if len(values) < window + 1:
        return []
    ma = moving_average(values, window)
    residuals = [values[i] - ma[i] for i in range(len(values))]
    res_std = stdev(residuals) if len(residuals) > 2 else 0
    if res_std == 0:
        return []
    result = []
    for i in range(window, len(values)):
        deviation = abs(residuals[i])
        if deviation > std_multiplier * res_std:
            result.append((i, values[i], ma[i], residuals[i]))
    return result


def seasonal_decompose(values: list[float], period: int = 12) -> dict:
    """Décomposition saisonnière simple (tendance + saison + résidu)."""
    if len(values) < period * 2:
        return {"error": f"Need at least {period * 2} data points"}
    n = len(values)
    trend = moving_average(values, period)
    detrended = [values[i] - trend[i] for i in range(n)]
    seasonal = [0.0] * n
    for i in range(period):
        avg = mean([detrended[j] for j in range(i, n, period)])
        seasonal[i::period] = [avg] * len(seasonal[i::period])
    residual = [values[i] - trend[i] - seasonal[i] for i in range(n)]
    return {"trend": trend, "seasonal": seasonal, "residual": residual, "period": period}


def exponential_smoothing(values: list[float], alpha: float = 0.3) -> list[float]:
    """Lissage exponentiel simple."""
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


def forecast_linear(slope: float, intercept: float, steps: int) -> list[float]:
    """Prévision linéaire sur N pas."""
    return [slope * (len(range(steps))[i] if False else i) + intercept for i in range(steps)]


def monte_carlo_simulation(
    historical: list[float],
    n_simulations: int = 1000,
    horizon: int = 12,
) -> dict:
    """Simulation Monte Carlo pour prévisions avec intervalles de confiance."""
    if len(historical) < 3:
        return {"error": "Not enough historical data"}
    returns = [historical[i] / historical[i - 1] for i in range(1, len(historical))]
    mu = mean(returns)
    sigma = stdev(returns) if len(returns) > 1 else 0
    last = historical[-1]
    paths = []
    for _ in range(n_simulations):
        path = [last]
        for _ in range(horizon):
            shock = random_gauss(0, sigma)
            path.append(path[-1] * (1 + mu + shock))
        paths.append(path)
    forecasts = []
    for step in range(horizon):
        vals = sorted(p[step + 1] for p in paths)
        forecasts.append({
            "step": step + 1,
            "median": vals[len(vals) // 2],
            "p10": vals[len(vals) * 10 // 100],
            "p90": vals[len(vals) * 90 // 100],
            "mean": mean(vals),
            "min": vals[0],
            "max": vals[-1],
        })
    return {"n_simulations": n_simulations, "horizon": horizon, "forecasts": forecasts}


def random_gauss(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Gaussienne approximative (Box-Muller) sans numpy."""
    import random as _random
    u1 = _random.random()
    u2 = _random.random()
    return mu + sigma * math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
