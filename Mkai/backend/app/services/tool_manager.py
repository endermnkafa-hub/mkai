"""
Tool Manager — LLM'in kullanabileceği araçları yönetir.

LLM'e yeteneklerini (web araması, hesaplama vb.) bildirir ve
LLM'den gelen araç çağırma isteklerini (tool calls) çalıştırır.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.services.knowledge_base import KnowledgeBase
from app.services.web_search_service import WebSearchService


class ToolManager:
    """LLM araç çağrılarını yöneten servis."""

    def __init__(
        self,
        web_search: WebSearchService | None = None,
        kb: KnowledgeBase | None = None,
    ) -> None:
        self.web_search = web_search or WebSearchService()
        self.kb = kb or KnowledgeBase()

    def get_tool_prompt(self) -> str:
        """LLM'e araç kullanımını anlatan system prompt parçası."""
        return """
[ARAÇ KULLANIMI]
Eğer soruyu cevaplamak için ekstra bilgiye veya hesaplamaya ihtiyacın varsa, aşağıdaki araçları kullanabilirsin.
Araç kullanmak için cevabında sadece aşağıdaki formattaki JSON bloğunu döndür (başka hiçbir şey yazma):

```json
{"tool": "arac_adi", "query": "arama_sorgusu"}
```

Kullanılabilir araçlar:
1. "web_search": Güncel bilgiler, ürün özellikleri (RTX 5070 vb.), haberler veya bilmediğin terimler için internette arama yapar. (Örn: {"tool": "web_search", "query": "NVIDIA RTX 5070 özellikleri"})
2. "calculate": Matematiksel hesaplamalar yapar. Sadece formül ver. (Örn: {"tool": "calculate", "query": "250 * 0.18"})

Eğer araç kullanmana gerek yoksa, doğrudan normal cevabını ver.
"""

    def parse_tool_call(self, llm_response: str) -> dict[str, str] | None:
        """LLM cevabından araç çağrısını çıkarır."""
        # JSON bloğunu bul
        match = re.search(r"```json\s*(\{.*?\})\s*```", llm_response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and "tool" in data and "query" in data:
                    return {"tool": str(data["tool"]), "query": str(data["query"])}
            except json.JSONDecodeError:
                pass
                
        # Bazen markdown olmadan direkt JSON dönebilir
        if llm_response.strip().startswith("{") and llm_response.strip().endswith("}"):
            try:
                 data = json.loads(llm_response.strip())
                 if isinstance(data, dict) and "tool" in data and "query" in data:
                     return {"tool": str(data["tool"]), "query": str(data["query"])}
            except json.JSONDecodeError:
                 pass
                 
        return None

    async def execute_tool(self, tool_call: dict[str, str]) -> str:
        """Belirtilen aracı çalıştırır ve sonucunu döndürür."""
        tool = tool_call.get("tool", "")
        query = tool_call.get("query", "")

        if not tool or not query:
            return "Hata: Geçersiz araç çağrısı."

        if tool == "web_search":
            result = await self.web_search.search(query)
            if result:
                 return f"[WEB ARAMASI SONUCU]\n{result}\n\nLütfen bu bilgileri kullanarak kullanıcıya cevap ver."
            return "[WEB ARAMASI SONUCU]\nSonuç bulunamadı. Lütfen bilmediğini belirt."

        elif tool == "calculate":
            result = self.kb.can_answer_directly(query)
            if result:
                return f"[HESAPLAMA SONUCU]\n{result}\n\nLütfen bu sonucu kullanıcıya ilet."
            return "[HESAPLAMA SONUCU]\nHesaplama yapılamadı."

        return f"Hata: Bilinmeyen araç '{tool}'."
