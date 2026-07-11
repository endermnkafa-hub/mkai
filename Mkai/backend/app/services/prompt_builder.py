from __future__ import annotations

import os
from typing import Any


class PromptBuilder:
    def __init__(self) -> None:
        self.default_language = os.getenv("DEFAULT_ASSISTANT_LANGUAGE", "tr")

    def build_system_prompt(self, *, user_language: str | None = None, route: str = "chat", code_prompt: str = "") -> str:
        language = (user_language or self.default_language).strip().lower()
        if language not in {"tr", "en", "de", "fr", "es", "it", "pt", "nl", "ja", "ko", "zh", "ru"}:
            language = "tr"

        if language == "tr":
            base = "Sen MKAI'sin. Kısa, net, doğru ve Türkçe cevap ver. Uydurma yapma; emin olmadığın yerde açıkça söyle."
        else:
            base = "You are MKAI. Reply briefly, clearly, accurately, and in the user's language. Do not hallucinate."

        if route == "code" and code_prompt:
            base = f"{base}\n\n{code_prompt}"
        return base

    def build_messages(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        *,
        user_language: str | None = None,
        memories: list[dict[str, Any]] | None = None,
        web_results: str = "",
        route: str = "chat",
        code_prompt: str = "",
        max_history: int = 8,
        max_memories: int = 5,
        max_web_results: int = 5,
    ) -> list[dict[str, str]]:
        language = (user_language or self.default_language).strip().lower()
        if language not in {"tr", "en", "de", "fr", "es", "it", "pt", "nl", "ja", "ko", "zh", "ru"}:
            language = "tr"

        normalized_history: list[dict[str, str]] = []
        for item in (history or [])[-max_history:]:
            role = str(item.get("role", "user"))
            content = str(item.get("content", "")).strip()
            if content:
                normalized_history.append({"role": role, "content": content})

        memory_block = ""
        if memories:
            short_memories = []
            for item in memories[:max_memories]:
                value = str(item.get("value", "")).strip()
                if value:
                    short_memories.append(f"- {value}")
            if short_memories:
                memory_block = "Kullanıcı bilgileri:\n" + "\n".join(short_memories)

        web_block = ""
        if web_results:
            web_lines = [line for line in web_results.splitlines() if line.strip()][:max_web_results * 3]
            web_block = "Güncel web bilgileri:\n" + "\n".join(web_lines[:max_web_results * 3])

        user_content = f"User language: {language}\nUser message: {message}"
        if memory_block:
            user_content = f"{user_content}\n\n{memory_block}"
        if web_block:
            user_content = f"{user_content}\n\n{web_block}"

        system_content = self.build_system_prompt(user_language=language, route=route, code_prompt=code_prompt)
        if memory_block:
            system_content = f"{system_content}\n\n{memory_block}"

        return [
            {"role": "system", "content": system_content},
            *normalized_history,
            {"role": "user", "content": user_content},
        ]
