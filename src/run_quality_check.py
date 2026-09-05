"""
run_quality_check.py
----------------------
Ponto de entrada CLI: lê a camada Gold (JSON — mesma estrutura dos
Projetos 01/03/04), roda o agente de qualidade e imprime o relatório.

Uso:
    export ANTHROPIC_API_KEY="sua_chave_aqui"
    python src/run_quality_check.py caminho/para/air_quality_daily.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from claude_client import ClaudeClient
from quality_agent import generate_quality_report


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python src/run_quality_check.py <caminho_para_gold.json>")
        sys.exit(1)

    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    client = ClaudeClient()
    report = generate_quality_report(rows, client)

    print(report)


if __name__ == "__main__":
    main()
