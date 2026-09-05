"""
Testes de quality_agent.py — a API do Claude é sempre substituída por
FakeClaudeClient. Nenhum teste aqui faz uma chamada de rede real.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quality_agent import generate_quality_report
from fake_claude_client import FakeClaudeClient


def _row(city, parameter, date, value):
    return {"city": city, "parameter": parameter, "measured_date": date, "avg_value": value}


def test_calls_client_with_formatted_anomalies():
    rows = [
        _row("São Paulo", "pm25", "2026-01-01", 20.0),
        _row("São Paulo", "pm25", "2026-01-02", 21.0),
        _row("São Paulo", "pm25", "2026-01-03", 19.0),
        _row("São Paulo", "pm25", "2026-01-04", 20.5),
        _row("São Paulo", "pm25", "2026-01-05", 85.0),
    ]
    client = FakeClaudeClient(canned_response="Relatório gerado.")

    report = generate_quality_report(rows, client)

    assert report == "Relatório gerado."
    assert len(client.calls) == 1
    user_message = client.calls[0]["user_message"]
    assert "São Paulo" in user_message
    assert "pm25" in user_message
    assert "85.0" in user_message


def test_system_prompt_is_loaded_from_file():
    rows = [_row("São Paulo", "pm25", "2026-01-01", 20.0)]
    client = FakeClaudeClient(canned_response="ok")

    generate_quality_report(rows, client)

    system_prompt = client.calls[0]["system"]
    assert "qualidade de dados" in system_prompt.lower()


def test_no_anomalies_still_calls_client_with_clear_message():
    rows = [
        _row("Rio de Janeiro", "o3", "2026-01-01", 30.0),
        _row("Rio de Janeiro", "o3", "2026-01-02", 31.0),
        _row("Rio de Janeiro", "o3", "2026-01-03", 29.5),
        _row("Rio de Janeiro", "o3", "2026-01-04", 30.2),
    ]
    client = FakeClaudeClient(canned_response="Tudo normal.")

    generate_quality_report(rows, client)

    assert "Nenhuma anomalia" in client.calls[0]["user_message"]
