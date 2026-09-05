"""
doc_agent.py
-------------
Orquestra o agente de documentação automática:
  1. Lê um arquivo .sql de um modelo dbt.
  2. Pede ao Claude para gerar a documentação no formato schema.yml.
  3. Valida que a resposta é YAML bem formado ANTES de considerá-la
     utilizável — um LLM pode "quase" acertar o formato, e texto
     malformado nunca deveria ir parar num arquivo de configuração do
     pipeline sem checagem.

Esse agente GERA uma sugestão de documentação para revisão humana —
não sobrescreve `schema.yml` automaticamente. Documentação incorreta
gerada por IA e aceita sem revisão é pior do que não ter documentação.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from claude_client import ClaudeClientProtocol

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "doc_generation_system.txt"


@dataclass
class DocGenerationResult:
    raw_response: str
    is_valid_yaml: bool
    parsed: dict | None
    error: str | None = None


def generate_model_docs(sql_path: Path, client: ClaudeClientProtocol) -> DocGenerationResult:
    sql_content = sql_path.read_text(encoding="utf-8")
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    user_message = f"Modelo: {sql_path.stem}\n\nSQL:\n```sql\n{sql_content}\n```"
    raw_response = client.complete(system=system_prompt, user_message=user_message)

    return _validate_yaml_response(raw_response)


def _validate_yaml_response(raw_response: str) -> DocGenerationResult:
    cleaned = _strip_markdown_fence(raw_response)
    try:
        parsed = yaml.safe_load(cleaned)
    except yaml.YAMLError as exc:
        return DocGenerationResult(raw_response=raw_response, is_valid_yaml=False, parsed=None, error=str(exc))

    if not isinstance(parsed, dict):
        return DocGenerationResult(
            raw_response=raw_response,
            is_valid_yaml=False,
            parsed=None,
            error="Resposta não é um mapeamento YAML válido no topo (esperado um dict).",
        )

    return DocGenerationResult(raw_response=raw_response, is_valid_yaml=True, parsed=parsed)


def _strip_markdown_fence(text: str) -> str:
    """Remove um bloco ```yaml ... ``` se o modelo envolver a resposta
    nele, apesar de instruído a não fazer isso — modelos de linguagem
    tendem a fazer isso de qualquer forma."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return stripped
