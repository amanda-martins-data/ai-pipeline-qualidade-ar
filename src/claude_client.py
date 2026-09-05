"""
claude_client.py
------------------
Camada fina sobre o SDK da Anthropic — deliberadamente isolada num
único módulo pequeno. Duas razões:

1. Testabilidade: `quality_agent.py` e `doc_agent.py` recebem esse
   client por injeção de dependência, então os testes usam um
   `FakeClaudeClient` e nunca fazem uma chamada de rede real.
2. Controle: se um dia for preciso trocar de modelo, adicionar retry,
   cache ou logging de custo/tokens, há um único lugar para mexer.

Requer a variável de ambiente ANTHROPIC_API_KEY. Sem ela, o client
falha imediatamente e com uma mensagem clara — não faz sentido deixar
o erro estourar 200 linhas depois, dentro de uma chamada de API.
"""

from __future__ import annotations

import os
from typing import Protocol

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 1024


class ClaudeClientProtocol(Protocol):
    """Interface mínima que `quality_agent` e `doc_agent` esperam.
    `FakeClaudeClient` (nos testes) e `ClaudeClient` (real) implementam
    a mesma interface — é isso que torna a injeção de dependência
    possível sem mocks pesados."""

    def complete(self, system: str, user_message: str) -> str: ...


class ClaudeClient:
    """Client real, que efetivamente chama a API da Anthropic."""

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY não definida. Exporte a variável de ambiente "
                "com uma API key válida antes de rodar os agentes de IA."
            )

        import anthropic  # import local: só é exigido de quem usa o client real

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def complete(self, system: str, user_message: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=0,  # determinismo: relatório de qualidade não é criatividade
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
