"""
Testes de anomaly_detection.py — sem IA, sem rede, 100% determinístico.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from anomaly_detection import detect_anomalies


def _row(city, parameter, date, value):
    return {"city": city, "parameter": parameter, "measured_date": date, "avg_value": value}


def test_detects_spike_above_baseline():
    rows = [
        _row("São Paulo", "pm25", "2026-01-01", 20.0),
        _row("São Paulo", "pm25", "2026-01-02", 21.0),
        _row("São Paulo", "pm25", "2026-01-03", 19.0),
        _row("São Paulo", "pm25", "2026-01-04", 20.5),
        _row("São Paulo", "pm25", "2026-01-05", 85.0),  # pico
    ]

    anomalies = detect_anomalies(rows)

    assert len(anomalies) == 1
    a = anomalies[0]
    assert a.city == "São Paulo"
    assert a.parameter == "pm25"
    assert a.direction == "acima"
    assert a.current_value == 85.0


def test_no_anomaly_when_stable():
    rows = [
        _row("Rio de Janeiro", "o3", "2026-01-01", 30.0),
        _row("Rio de Janeiro", "o3", "2026-01-02", 31.0),
        _row("Rio de Janeiro", "o3", "2026-01-03", 29.5),
        _row("Rio de Janeiro", "o3", "2026-01-04", 30.2),
    ]

    anomalies = detect_anomalies(rows)

    assert anomalies == []


def test_ignores_series_with_insufficient_history():
    rows = [
        _row("Belo Horizonte", "pm10", "2026-01-01", 40.0),
        _row("Belo Horizonte", "pm10", "2026-01-02", 90.0),
    ]

    anomalies = detect_anomalies(rows, min_baseline_points=3)

    assert anomalies == []


def test_ignores_constant_series_zero_stdev():
    rows = [
        _row("São Paulo", "co", "2026-01-01", 1.0),
        _row("São Paulo", "co", "2026-01-02", 1.0),
        _row("São Paulo", "co", "2026-01-03", 1.0),
        _row("São Paulo", "co", "2026-01-04", 1.0),
    ]

    anomalies = detect_anomalies(rows)

    assert anomalies == []


def test_detects_drop_below_baseline():
    rows = [
        _row("São Paulo", "pm25", "2026-01-01", 40.0),
        _row("São Paulo", "pm25", "2026-01-02", 42.0),
        _row("São Paulo", "pm25", "2026-01-03", 39.0),
        _row("São Paulo", "pm25", "2026-01-04", 41.0),
        _row("São Paulo", "pm25", "2026-01-05", 2.0),  # queda brusca (sensor offline?)
    ]

    anomalies = detect_anomalies(rows)

    assert len(anomalies) == 1
    assert anomalies[0].direction == "abaixo"


def test_multiple_series_sorted_by_relevance():
    rows = [
        _row("A", "pm25", "2026-01-01", 19.0),
        _row("A", "pm25", "2026-01-02", 21.0),
        _row("A", "pm25", "2026-01-03", 20.0),
        _row("A", "pm25", "2026-01-04", 19.5),
        _row("A", "pm25", "2026-01-05", 26.0),  # anomalia leve
        _row("B", "pm25", "2026-01-01", 19.0),
        _row("B", "pm25", "2026-01-02", 21.0),
        _row("B", "pm25", "2026-01-03", 20.0),
        _row("B", "pm25", "2026-01-04", 19.5),
        _row("B", "pm25", "2026-01-05", 200.0),  # anomalia extrema
    ]

    anomalies = detect_anomalies(rows, z_threshold=1.5)

    assert len(anomalies) == 2
    assert anomalies[0].city == "B"  # a mais extrema vem primeiro
