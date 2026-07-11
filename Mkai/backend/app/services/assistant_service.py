"""
Assistant Service — MKAI v3 Pipeline'ın ana entegrasyon noktası.

Pipeline:
Message → Router → [Direct/Web/Memory/Code] → Tool Manager → Prompt → LLM → Self Check → Response
"""
from __future__ import annotations

import os
import re
from typing import Any

from app.core.exceptions import AppError
from app.providers.router import router as provider_router
from app.schemas.chat import ChatRequest, ChatResponse

from app.services.core_brain_service import CoreBrainService, BrainContext
from app.services.memory_service import MemoryService
from app.services.message_router import MessageRouter, RouteType
from app.services.knowledge_base import KnowledgeBase
from app.services.web_search_service import WebSearchService
from app.services.code_agent import CodeAgent
from app.services.conversation_manager import ConversationManager
from app.services.tool_manager import ToolManager
from app.services.self_check import SelfCheck


class AssistantService:
    def __init__(self) -> None:
        self.model_name = os.getenv("DEFAULT_MODEL", "qwen2.5:14b")
        
        # v3 Servisleri başlat
        self.kb = KnowledgeBase()
        self.web_search = WebSearchService()
        self.code_agent = CodeAgent()
        self.conv_manager = ConversationManager()
        self.msg_router = MessageRouter(kb=self.kb)
        self.tool_manager = ToolManager(web_search=self.web_search, kb=self.kb)
        self.self_check = SelfCheck()
        self.core_brain = CoreBrainService()

    async def generate_reply(
        self,
        request: ChatRequest,
        history: list[dict[str, str]] | None = None,
        db: Any | None = None,
    ) -> ChatResponse:
        message = request.message.strip()
        if not message:
            raise AppError("Message cannot be empty", status_code=400)

        # 1. Geçmişi Hazırla
        prompt_history = self._prepare_history(request, history)
        
        user_id = getattr(request, "user_id", None) or "anonymous"
        workspace = getattr(request, "workspace", None)
        user_language = self._detect_language(message, prompt_history)

        # 2. Konuşma Bağlamı Çıkar (Conversation Manager)
        conv_context = self.conv_manager.analyze(message, history=prompt_history)
        resolved_message = conv_context.resolved_message or message

        # 3. Hafıza İşlemleri (Çıkarma & Arama)
        memories = []
        if db is not None:
            memory_service = MemoryService(db)
            memory_service.extract_and_store(message, user_id=user_id, workspace=workspace)
            memories = [
                item.to_dict() for item in memory_service.search_relevant_memories(user_id, message=resolved_message, workspace=workspace, max_results=5)
            ]
            if not memories:
                memories = [item.to_dict() for item in memory_service.list_memories(user_id)]

        # 4. Yönlendirme ve Karar Verme (Message Router)
        route_decision = self.msg_router.route(resolved_message, memories=memories)

        # 5. Direct Answer Kontrolü (LLM bypass)
        if route_decision.route == RouteType.DIRECT and db is None:
            direct_ans = self.kb.can_answer_directly(resolved_message)
            if direct_ans:
                return ChatResponse(reply=direct_ans, model="direct-kb")

        # 6. Web Arama Kararı
        web_results = ""
        web_used = False
        needs_web = self.web_search.should_search(
            resolved_message, 
            confidence=route_decision.confidence, 
            route=route_decision.route,
            knowledge_hit=route_decision.route == RouteType.KNOWLEDGE
        )
        
        if needs_web:
            search_q = route_decision.search_query or resolved_message
            web_results = await self.web_search.search(search_q, lang=user_language)
            web_used = bool(web_results)
            
            # HALLUCINATION GUARD
            # Eğer modelin confidence'ı çok düşükse veya bilgi kesin web'den gelmeliyse ve web başarısız olduysa
            if not web_used and (route_decision.confidence < 0.60 or route_decision.route == RouteType.WEB):
                fallback_msg = "Bunun doğruluğundan emin değilim. Güncel bilgiye şu an ulaşamadım."
                if user_language == "en":
                    fallback_msg = "I am not entirely sure about this. I couldn't reach the latest information right now."
                return ChatResponse(reply=fallback_msg, model="hallucination-guard")

        # 7. Koda Özel Talimatlar
        code_prompt = ""
        if route_decision.route == RouteType.CODE:
            code_ctx = self.code_agent.analyze(resolved_message)
            code_prompt = self.code_agent.build_code_prompt(code_ctx, resolved_message)

        # 8. Brain Context ve Prompt Oluşturma
        brain_context = BrainContext(
            user_id=user_id,
            workspace=workspace,
            message=resolved_message,
            history=prompt_history,
            memories=memories,
            decision=route_decision,
            conv_context=conv_context,
            debug={"confidence": route_decision.confidence, "route": route_decision.route}
        )

        brain_service = CoreBrainService(db) if db is not None else self.core_brain
        messages = brain_service.build_prompt(
            brain_context,
            user_language=user_language,
            web_results=web_results,
            tools_prompt=self.tool_manager.get_tool_prompt(),
            code_prompt=code_prompt,
        )

        provider = getattr(request, "provider", None) or "ollama"
        model = getattr(request, "model", None) or self.model_name

        if db is not None and not memories:
            memories = [item.to_dict() for item in MemoryService(db).list_memories(user_id)]

        # 9. LLM Çağrısı 
        async def call_llm(msgs):
            return await provider_router.generate(msgs, provider=provider, model=model)

        try:
            result = await call_llm(messages)
            reply = str(result.get("text", "")).strip()
            
            # 10. Tool Çağrısı Kontrolü
            tool_call = self.tool_manager.parse_tool_call(reply)
            if tool_call:
                tool_res = await self.tool_manager.execute_tool(tool_call)
                # Aracı çalıştırıp sonucu prompta ekleyip tekrar çağır
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": tool_res})
                result = await call_llm(messages)
                reply = str(result.get("text", "")).strip()

            if not reply:
                raise AppError("Empty response from LLM", status_code=502)

            # 11. Self Check
            check_result = await self.self_check.check(
                question=resolved_message,
                answer=reply,
                route=route_decision.route,
                web_used=web_used,
                provider_fn=call_llm
            )
            
            if not check_result.passed and check_result.retry_with_web and not web_used:
                # Fallback: Cevap kötü ve web araması yapılmamışsa, web araması yapıp tekrar dene
                web_results = await self.web_search.search(resolved_message, lang=user_language)
                if web_results:
                    messages = brain_service.build_prompt(
                        brain_context,
                        user_language=user_language,
                        web_results=web_results,
                        tools_prompt="",
                        code_prompt=code_prompt,
                    )
                    result = await call_llm(messages)
                    reply = str(result.get("text", "")).strip()

        except Exception as exc:
            raise AppError(f"LLM request failed: {exc}", status_code=502) from exc

        # 12. Post Processing (Temizlik)
        reply = self._post_process(reply, message, user_language)

        return ChatResponse(reply=reply, model=str(result.get("model", self.model_name)))

    def _prepare_history(self, request: ChatRequest, history: list[dict[str, str]] | None) -> list[dict[str, str]]:
        prompt_history: list[dict[str, str]] = []
        if history:
            prompt_history = [{"role": str(i.get("role", "user")), "content": str(i.get("content", ""))} for i in history if isinstance(i, dict)]
        elif getattr(request, "history", None):
            prompt_history = [{"role": str(i.get("role", "user")), "content": str(i.get("content", ""))} for i in request.history if isinstance(i, dict)]
        return prompt_history[-16:]  # Son 8 tur

    def _post_process(self, reply: str, original_message: str, lang: str) -> str:
        # Düşünce bloklarını temizle
        reply = re.sub(r"\[PLAN:.*?\]|<thinking>.*?</thinking>|<reasoning>.*?</reasoning>", "", reply, flags=re.DOTALL).strip()
        for tag in ["[PLAN:", "<thinking>", "<reasoning>"]:
            if tag in reply:
                reply = reply.split(tag)[0].strip()
        reply = reply.replace("</thinking>", "").replace("</reasoning>", "").strip()

        # Selamlaşma tekrarlarını temizle
        greeting_words = ["selam", "merhaba", "s.a", "aleyküm", "aleykum", "hey", "hi", "hello"]
        has_greeting = any(g in original_message.lower() for g in greeting_words)
        if not has_greeting:
            reply = re.sub(r"(?:ve\s+)?aleyk[üu]m\s+selam\s*!?(?:\s*😊)?(?:\s*nas[ıi]ls[ıi]n\s*\??)?", "", reply, flags=re.IGNORECASE).strip()
            reply = re.sub(r"(?:ve\s+)?aleyk[üu]m\s+selam\s*[,.]\s*", "", reply, flags=re.IGNORECASE).strip()
            reply = reply.replace("🌟", "").strip()

        # Robotik, yapay zeka özür ve yasaklı kalıpları temizle
        forbidden_patterns = [
            r"[Hh]af[ıi]zam(?:da|dan|a)\s+(?:buldum|kaydettim|sakladım|göre|kayıtlı|bulunuyor)[^.]*\.?",
            r"[Kk]ay[ıi]tlar[ıi]ma\s+g[öo]re[^.]*\.?",
            r"[Öö]nceki\s+konu[şs]mam[ıi]za\s+g[öo]re[^.]*\.?",
            r"[Aa]s\s+an\s+AI[^.]*\.?",
            r"[Yy]apay\s+zeka\s+olarak[^.]*\.?",
            r"Ben\s+bir\s+yapay\s+zeka[yı]ım[^.]*\.?",
            r"[Öö]z[üu]r\s+dilerim,[^.]*\.",
            r"[Mm]aalesef[,]?[^.]*\.",
        ]
        for pattern in forbidden_patterns:
            reply = re.sub(pattern, "", reply).strip()

        # Language Guard (Çince kontrolü ve dil tutarlılığı)
        if re.search(r"[\u4e00-\u9fff]", reply):
            # Çince karakter tespit edildi
            return "Üzgünüm, yanıt üretirken dil modeli bir hata yaptı (dil kilitlenmesi). Lütfen tekrar dener misin?"
            
        reply_lang = self._detect_language(reply)
        if lang == "tr" and reply_lang == "en":
            # Kullanıcı Türkçe istedi ama cevap komple İngilizce çıktı
            # Yarı İngilizce/Türkçe durumları için _detect_language zaten kelime sayıyor
            return "Üzgünüm, sadece Türkçe yanıt verebilirim. (Language Guard)"

        # Siz -> Sen dönüşümü (Türkçe yanıtlarda)
        if lang == "tr":
            siz_replacements = [
                (r"\b[Ss]izin\b", lambda m: "Senin" if m.group().istitle() else "senin"),
                (r"\b[Ss]izce\b", lambda m: "Sence" if m.group().istitle() else "sence"),
                (r"\b[Ss]ize\b", lambda m: "Sana" if m.group().istitle() else "sana"),
                (r"\b[Ss]iz\b", lambda m: "Sen" if m.group().istitle() else "sen"),
                (r"\b[Ss]izden\b", lambda m: "Senden" if m.group().istitle() else "senden"),
                (r"\b[Ss]iyle\b", lambda m: "Seninle" if m.group().istitle() else "seninle"),
                (r"\b[Ss]iniz\b", lambda m: "Sun" if m.group().istitle() else "sun"),
                (r"\b[Ss]inizin\b", lambda m: "Senin" if m.group().istitle() else "senin"),
                (r"en\s+sevdiğiniz", "en sevdiğin"),
                (r"nasılsınız", "nasılsın"),
            ]
            for pat, replacement in siz_replacements:
                reply = re.sub(pat, replacement, reply)

        reply = re.sub(r"\s+", " ", reply).strip()
        if (reply.startswith('"') and reply.endswith('"')) or (reply.startswith("'") and reply.endswith("'")):
            reply = reply[1:-1].strip()

        return reply

    def _detect_language(self, message: str, history: list[dict[str, str]] | None = None) -> str:
        text = message.lower()
        combined = f"{text} {' '.join(item.get('content', '') for item in (history or [])).lower()}"
        if re.search(r"[çğışöüÇĞİŞÖÜ]", message): return "tr"
        tr_tokens = ["merhaba", "nasıl", "neden", "bugün", "bu", "şu", "evet", "hayır"]
        en_tokens = ["hello", "why", "today", "what", "how", "yes", "no"]
        return "tr" if sum(1 for t in tr_tokens if t in combined) >= sum(1 for t in en_tokens if t in combined) else "en"

assistant_service = AssistantService()
