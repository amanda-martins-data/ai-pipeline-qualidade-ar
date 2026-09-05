"""
run_doc_generation.py
-----------------------
Ponto de entrada CLI: gera uma SUGESTÃO de documentação para um modelo
SQL do dbt, para revisão humana (não escreve automaticamente).

Uso:
    export ANTHROPIC_API_KEY="sua_chave_aqui"
    python src/run_doc_generation.py caminho/para/modelo.sql
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from claude_client import ClaudeClient
from doc_agent import generate_model_docs


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python src/run_doc_generation.py <caminho_para_modelo.sql>")
        sys.exit(1)

    sql_path = Path(sys.argv[1])
    client = ClaudeClient()
    result = generate_model_docs(sql_path, client)

    if not result.is_valid_yaml:
        print(f"⚠️  O modelo gerou uma resposta que NÃO é YAML válido: {result.error}")
        print("--- resposta bruta (para depuração manual) ---")
        print(result.raw_response)
        sys.exit(2)

    print(f"# Sugestão de documentação para {sql_path.stem} — REVISE antes de aplicar")
    print(yaml.dump(result.parsed, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    main()
