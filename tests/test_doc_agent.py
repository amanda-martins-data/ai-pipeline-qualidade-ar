"""
Testes de doc_agent.py — cobrindo especialmente o caso que mais importa:
o agente precisa REJEITAR respostas do LLM que não são YAML válido, em
vez de deixar passar documentação quebrada para o repositório.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from doc_agent import generate_model_docs
from fake_claude_client import FakeClaudeClient

SAMPLE_SQL = "select city, avg(value) as avg_value from stg_air_quality group by 1"


def test_accepts_valid_yaml_response(tmp_path):
    sql_file = tmp_path / "sample_model.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")

    valid_yaml = (
        "description: Agrega o valor médio por cidade.\n"
        "columns:\n"
        "  - name: city\n"
        "    description: Nome da cidade.\n"
        "  - name: avg_value\n"
        "    description: Valor médio agregado.\n"
    )
    client = FakeClaudeClient(canned_response=valid_yaml)

    result = generate_model_docs(sql_file, client)

    assert result.is_valid_yaml is True
    assert result.error is None
    assert result.parsed["description"].startswith("Agrega")
    assert len(result.parsed["columns"]) == 2


def test_strips_markdown_fence_before_validating(tmp_path):
    sql_file = tmp_path / "sample_model.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")

    fenced_yaml = "```yaml\ndescription: teste\ncolumns: []\n```"
    client = FakeClaudeClient(canned_response=fenced_yaml)

    result = generate_model_docs(sql_file, client)

    assert result.is_valid_yaml is True
    assert result.parsed["description"] == "teste"


def test_rejects_malformed_yaml(tmp_path):
    sql_file = tmp_path / "sample_model.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")

    broken_yaml = "description: [isso não fecha a lista\ncolumns: - sem indentação certa"
    client = FakeClaudeClient(canned_response=broken_yaml)

    result = generate_model_docs(sql_file, client)

    assert result.is_valid_yaml is False
    assert result.parsed is None
    assert result.error is not None


def test_rejects_response_that_is_not_a_mapping(tmp_path):
    sql_file = tmp_path / "sample_model.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")

    client = FakeClaudeClient(canned_response="apenas um texto solto, não é YAML estruturado")

    result = generate_model_docs(sql_file, client)

    assert result.is_valid_yaml is False


def test_prompt_includes_the_actual_sql_content(tmp_path):
    sql_file = tmp_path / "sample_model.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")
    client = FakeClaudeClient(canned_response="description: x\ncolumns: []")

    generate_model_docs(sql_file, client)

    assert SAMPLE_SQL in client.calls[0]["user_message"]
    assert "sample_model" in client.calls[0]["user_message"]
