"""
anomaly_detection.py
---------------------
Detecção de anomalias em Python puro e determinístico — deliberadamente
SEM chamar nenhum LLM aqui. Um modelo de linguagem não deveria fazer
aritmética por conta própria; ele é bom em explicar em português claro
o que a estatística já encontrou. Essa separação é a decisão central
deste projeto (ver docs/architecture.md).

Método: comparação do valor do dia mais recente contra a média e o
desvio padrão dos N dias anteriores (z-score). Sem numpy/scipy — só
biblioteca padrão, para manter o pacote de deploy mínimo.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from itertools import groupby


@dataclass
class Anomaly:
    city: str
    parameter: str
    measured_date: str
    current_value: float
    baseline_mean: float
    baseline_stdev: float
    z_score: float
    severity: str  # "moderada" ou "alta"
    direction: str  # "acima" ou "abaixo"


def _severity_from_z(z: float) -> str:
    return "alta" if abs(z) >= 3 else "moderada"


def detect_anomalies(
    rows: list[dict],
    z_threshold: float = 2.0,
    min_baseline_points: int = 3,
) -> list[Anomaly]:
    """Recebe as linhas da camada Gold (uma por cidade+poluente+dia,
    já ordenadas por measured_date) e retorna anomalias no dia mais
    recente de cada série (cidade, poluente).

    Uma série com menos de `min_baseline_points` dias de histórico é
    ignorada — não dá para calcular desvio padrão confiável com poucos
    pontos, e um "falso alarme" por dado insuficiente é pior do que
    não alertar.
    """
    anomalies: list[Anomaly] = []

    keyfunc = lambda r: (r["city"], r["parameter"])
    sorted_rows = sorted(rows, key=lambda r: (r["city"], r["parameter"], r["measured_date"]))

    for (city, parameter), group_iter in groupby(sorted_rows, key=keyfunc):
        series = list(group_iter)
        if len(series) < min_baseline_points + 1:
            continue

        *baseline, latest = series
        baseline_values = [r["avg_value"] for r in baseline]

        mean = statistics.mean(baseline_values)
        stdev = statistics.pstdev(baseline_values)

        if stdev == 0:
            continue  # série constante: qualquer desvio não é comparável por z-score

        z = (latest["avg_value"] - mean) / stdev
        if abs(z) < z_threshold:
            continue

        anomalies.append(
            Anomaly(
                city=city,
                parameter=parameter,
                measured_date=latest["measured_date"],
                current_value=latest["avg_value"],
                baseline_mean=round(mean, 2),
                baseline_stdev=round(stdev, 2),
                z_score=round(z, 2),
                severity=_severity_from_z(z),
                direction="acima" if z > 0 else "abaixo",
            )
        )

    return sorted(anomalies, key=lambda a: abs(a.z_score), reverse=True)
