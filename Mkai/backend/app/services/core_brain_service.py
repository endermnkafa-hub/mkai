from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.memory_service import MemoryService
from app.services.message_router import RouteDecision, RouteType
from app.services.conversation_manager import ConversationContext


@dataclass
class BrainContext:
    user_id: str
    workspace: str | None
    message: str
    history: list[dict[str, str]] = field(default_factory=list)
    profile: dict[str, Any] = field(default_factory=dict)
    memories: list[dict[str, Any]] = field(default_factory=list)
    decision: RouteDecision = field(default_factory=lambda: RouteDecision(RouteType.CHAT, 1.0, "general"))
    conv_context: ConversationContext | None = None
    debug: dict[str, Any] = field(default_factory=dict)


class CoreBrainService:
    def __init__(self, db: Any | None = None) -> None:
        self.db = db

    def analyze(self, message: str, *, user_id: str | None = None, workspace: str | None = None) -> BrainContext:
        user_id = user_id or "anonymous"
        memories: list[dict[str, Any]] = []
        if self.db is not None:
            memory_service = MemoryService(self.db)
            memories = [item.to_dict() for item in memory_service.search_relevant_memories(user_id, message=message, workspace=workspace, max_results=5)]

        decision = RouteDecision(
            route=RouteType.MEMORY if memories else RouteType.CHAT,
            confidence=0.90 if memories else 0.70,
            domain="general",
            needs_memory=bool(memories),
            needs_web_search=False,
        )

        return BrainContext(
            user_id=user_id,
            workspace=workspace,
            message=message,
            profile={"user_id": user_id, "workspace": workspace},
            memories=memories,
            decision=decision,
        )

    def build_prompt(
        self,
        context: BrainContext,
        *,
        user_language: str | None = None,
        web_results: str = "",
        tools_prompt: str = "",
        code_prompt: str = "",
    ) -> list[dict[str, str]]:
        lang = user_language or "tr"
        memory_block = self._format_memories_natural(context.memories, lang=lang)
        route_name = context.decision.route.value if hasattr(context.decision.route, "value") else str(context.decision.route)

        system_prompt = self._build_system_prompt(
            memory_block,
            lang=lang,
            workspace=context.workspace,
            route=route_name,
            message=context.message,
            tools_prompt=tools_prompt,
            code_prompt=code_prompt,
        )

        user_content = context.message
        
        # Konuşma bağlamı ekle
        if context.conv_context:
            context_str = ""
            if context.conv_context.topic != "general":
                context_str += f"Konu: {context.conv_context.topic}\n"
            if context.conv_context.references:
                context_str += f"Bahsedilenler: {', '.join(context.conv_context.references[-3:])}\n"
            
            if context_str:
                user_content = f"[{context_str.strip()}]\n\n{context.conv_context.resolved_message or context.message}"

        # Web arama sonuçları varsa
        if web_results:
            if lang == "tr":
                user_content = (
                    f"{user_content}\n\n"
                    f"[Aşağıdaki web arama sonuçlarını kullanarak cevap ver. Doğrudan bilgiyi sun, 'webde buldum' deme]:\n{web_results}"
                )
            else:
                user_content = (
                    f"{user_content}\n\n"
                    f"[Use these web search results to answer. Present facts directly, don't say 'I found on web']:\n{web_results}"
                )

        return [
            {"role": "system", "content": system_prompt},
            *context.history,
            {"role": "user", "content": user_content},
        ]

    def _build_system_prompt(
        self,
        memory_block: str,
        *,
        lang: str,
        workspace: str | None,
        route: str,
        message: str,
        tools_prompt: str,
        code_prompt: str,
    ) -> str:
        lowered_msg = message.lower()
        if lang == "tr":
            identity = (
                "Sen Muhammed'in kişisel asistanı MKAI'sin. "
                "MKAI, your personal AI operating system and lifelong assistant. "
                "Samimi, zeki ve dürüst bir asistansın. "
                "Emin olmadığın konularda uydurma yapmaz, 'tam emin değilim' dersin. "
                "Asla 'Özür dilerim', 'Ben bir yapay zekayım' gibi robotik cümleler kurma."
            )

            rules = [
                "ZORUNLU KURALLAR:",
                "1. DİL: Her zaman ve sadece Türkçe yanıt ver (kullanıcı açıkça başka bir dil istemedikçe).",
                "2. DİL KİLİDİ: Asla dilleri birbirine karıştırma. Asla Çince veya İngilizce (istenmedikçe) cevap üretme.",
                "3. HAFIZA GİZLİLİĞİ: 'Hafıza', 'kayıt' kelimelerini ASLA kullanma. Bilgiyi doğrudan söyle.",
                "4. DÜRÜSTLÜK: Emin olmadığın hiçbir bilgiyi uydurma.",
            ]

            if route == "code" and code_prompt:
                rules.append(code_prompt)
            elif route == "knowledge":
                rules.append("4. ÖĞRETME: Terimi açıklarken kısa, net ve anlaşılır ol.")
                
            instructions = "\n".join(rules)
        else:
            identity = (
                "You are MKAI - Muhammed's personal AI assistant. "
                "MKAI, your personal AI operating system and lifelong assistant. "
                "You are smart, helpful, and honest. If you are not sure, say you don't know, never hallucinate. "
                "Never say 'I am just an AI' or 'I apologize'."
            )

            rules = [
                "RULES:",
                "1. LANGUAGE: Respond in fluent English. Use 'you'.",
                "2. MEMORY: Keep memory invisible. State facts directly.",
                "3. HONESTY: Never hallucinate facts if you are unsure.",
            ]

            if route == "code" and code_prompt:
                rules.append(code_prompt)
            elif route == "knowledge":
                rules.append("4. TEACHING: Explain the term clearly and concisely.")

            instructions = "\n".join(rules)

        workspace_note = f"\nAktif calisma alani: {workspace}" if workspace else ""
        
        parts = [identity, instructions.strip()]
        if tools_prompt:
            parts.append(tools_prompt)
        if memory_block:
            parts.append(memory_block)
            parts.append("Kullanıcı bilgilerini doğrudan cevaplarında kullan; geçmişe ait bir hatırlatma gibi konuşma.")
        if workspace_note:
            parts.append(workspace_note)

        return "\n\n".join(parts)

    def _format_memories_natural(self, memories: list[dict[str, Any]], *, lang: str) -> str:
        if not memories:
            return ""

        facts: list[str] = []
        seen: set[str] = set()

        for item in memories:
            value = str(item.get("value", "")).strip()
            if not value or value in seen:
                continue
            seen.add(value)

            if lang == "tr":
                val_lower = value.lower()
                if "kullanicinin adi" in val_lower or "kullanıcının adı" in val_lower:
                    parts = re.split(r"ad[ıi]m?|ad[ıi]\s+", value, flags=re.IGNORECASE)
                    name = parts[-1].strip() if len(parts) > 1 else value
                    val = f"Karşındaki kullanıcının adı {name}'dir."
                elif "favori renk:" in val_lower:
                    color = value.split(":")[-1].strip()
                    val = f"Karşındaki kullanıcının en sevdiği renk {color}'dir."
                elif "kullanicinin yasi" in val_lower or "kullanıcının yaşı" in val_lower:
                    parts = re.split(r"ya[şs]ı\s+|yasi\s+", value, flags=re.IGNORECASE)
                    age = parts[-1].strip() if len(parts) > 1 else value
                    val = f"Karşındaki kullanıcının yaşı {age}'dir."
                elif "yasadigi yer:" in val_lower:
                    loc = value.split(":")[-1].strip()
                    val = f"Karşındaki kullanıcı {loc}'da yaşıyor."
                elif "ogreniyor:" in val_lower or "öğreniyor:" in val_lower:
                    subj = value.split(":")[-1].strip()
                    val = f"Karşındaki kullanıcı {subj} öğreniyor."
                else:
                    val = f"Kullanıcı hakkında bilgi: {value}"
            else:
                val_lower = value.lower()
                if "kullanicinin adi" in val_lower or "name" in val_lower:
                    name = value.split("adi")[-1].strip().split("name")[-1].strip()
                    val = f"The user's name is {name}."
                elif "color" in val_lower:
                    color = value.split(":")[-1].strip()
                    val = f"The user's favorite color is {color}."
                else:
                    val = f"Fact about the user: {value}"

            facts.append(f"- {val}")

        if not facts:
            return ""

        if lang == "tr":
            header = "\nKarşındaki kullanıcı hakkında bilmen gerekenler (bunları doğrudan cevaplarında kullan, asla geçmişe atıfta bulunma):"
        else:
            header = "\nFacts about the user you are talking to (use directly in answers, never refer to memory):"

        return header + "\n" + "\n".join(facts)
