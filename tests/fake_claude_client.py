"""
FakeClaudeClient — implementa a mesma interface de claude_client.ClaudeClient
(via duck typing / Protocol) sem nenhuma chamada de rede. Usado por todos
os testes de `quality_agent` e `doc_agent`.
"""


class FakeClaudeClient:
    def __init__(self, canned_response: str = ""):
        self.canned_response = canned_response
        self.calls: list[dict] = []

    def complete(self, system: str, user_message: str) -> str:
        self.calls.append({"system": system, "user_message": user_message})
        return self.canned_response
