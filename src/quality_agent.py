"""
quality_agent.py
------------------
Orquestra o agente de qualidade de dados:
  1. Roda `anomaly_detection.detect_anomalies` (determinístico, sem IA).
  2. Se houver anomalias, monta um prompt com os números encontrados e
     pede ao Claude para escrever a explicação em linguagem natural.

Separação deliberada: a MATEMÁTICA é sempre determinística e testável
sem IA. O LLM só entra para traduzir números já corretos em texto
compreensível — nunca para decidir o que é ou não uma anomalia.
"""

from __future__ import annotations

from pathlib import Path

from anomaly_detection import Anomaly, detect_anomalies
from claude_client import ClaudeClientProtocol

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "quality_report_system.txt"


def _format_anomalies_for_prompt(anomalies: list[Anomaly]) -> str:
    if not anomalies:
        return "Nenhuma anomalia detectada nos dados de hoje."

    lines = ["Anomalias detectadas (ordenadas por relevância):", ""]
    for a in anomalies:
        lines.append(
            f"- Cidade: {a.city} | Poluente: {a.parameter} | Data: {a.measured_date}\n"
            f"  Valor observado: {a.current_value} | Média dos dias anteriores: {a.baseline_mean} "
            f"(desvio padrão: {a.baseline_stdev})\n"
            f"  Direção: {a.direction} do normal | Severidade: {a.severity}"
        )
    return "\n".join(lines)


def generate_quality_report(rows: list[dict], client: ClaudeClientProtocol) -> str:
    """Gera o relatório de qualidade em linguagem natural.

    `rows` é a mesma estrutura da camada Gold dos Projetos 01/03/04
    (city, parameter, measured_date, avg_value, ...), com histórico
    suficiente para calcular baseline.
    """
    anomalies = detect_anomalies(rows)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_message = _format_anomalies_for_prompt(anomalies)

    return client.complete(system=system_prompt, user_message=user_message)
