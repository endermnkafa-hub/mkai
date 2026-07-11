"""Simple five-route router for MKAI v4."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.services.knowledge_base import KnowledgeBase


class RouteType(str, Enum):
    DIRECT = "direct"
    CHAT = "chat"
    WEB = "web"
    MEMORY = "memory"
    CODE = "code"


@dataclass
class RouteDecision:
    route: str
    confidence: float
    domain: str
    search_query: str | None = None
    needs_memory: bool = False
    needs_web_search: bool = False


class MessageRouter:
    def __init__(self, kb: KnowledgeBase | None = None) -> None:
        self.kb = kb or KnowledgeBase()

    def route(self, message: str, *, memories: list[Any] | None = None) -> RouteDecision:
        lowered = message.lower().strip()
        memories = memories or []

        if self._is_direct_answer(message, lowered):
            return RouteDecision(route=RouteType.DIRECT, confidence=1.0, domain="general")

        if self._is_memory_query(lowered, memories):
            return RouteDecision(
                route=RouteType.MEMORY,
                confidence=0.92 if memories else 0.38,
                domain="general",
                needs_memory=True,
            )

        if self._is_code_request(lowered):
            return RouteDecision(route=RouteType.CODE, confidence=0.86, domain="programming")

        domain = self._detect_domain(lowered)
        if self._needs_web(lowered):
            return RouteDecision(
                route=RouteType.WEB,
                confidence=0.34,
                domain=domain,
                search_query=message,
                needs_web_search=True,
            )

        confidence = 0.75 if len(lowered.split()) > 2 else 0.58
        return RouteDecision(route=RouteType.CHAT, confidence=confidence, domain=domain)

    def _is_direct_answer(self, message: str, lowered: str) -> bool:
        if not message.strip():
            return False
        if self._is_greeting(lowered):
            return True
        if self._is_simple_math(lowered):
            return True
        if self._is_unit_conversion(lowered):
            return True
        if self._is_minecraft_command(lowered):
            return True
        if self._is_known_game_term(lowered):
            return True
        if len(message.split()) <= 3 and not any(q in lowered for q in ["?", "nedir", "nasıl", "hangi", "neden"]):
            return True
        return False

    def _is_greeting(self, lowered: str) -> bool:
        greetings = {
            "selam", "merhaba", "sa", "s.a", "günaydın", "iyi geceler", "naber", "nasılsın", "hello", "hi", "hey",
        }
        return lowered in greetings or any(word in lowered for word in greetings)

    def _is_simple_math(self, lowered: str) -> bool:
        if re.fullmatch(r"\d+(?:\.\d+)?\s*[\+\-\*/]\s*\d+(?:\.\d+)?", lowered):
            return True
        return bool(re.search(r"\b(?:topla|çıkar|çarp|böl|artı|eksi)\b", lowered)) and re.search(r"\d", lowered)

    def _is_unit_conversion(self, lowered: str) -> bool:
        conversions = {
            ("km", "m"): 1000.0,
            ("m", "cm"): 100.0,
            ("cm", "m"): 0.01,
            ("kg", "g"): 1000.0,
            ("g", "kg"): 0.001,
            ("l", "ml"): 1000.0,
            ("ml", "l"): 0.001,
        }
        for (source, target), _ in conversions.items():
            if re.search(rf"\b\d+(?:\.\d+)?\s*{re.escape(source)}\b", lowered) and re.search(rf"\b(?:kaç|to|in|=)?\s*{re.escape(target)}\b", lowered):
                return True
        return False

    def _is_minecraft_command(self, lowered: str) -> bool:
        if not lowered.startswith("/"):
            return False
        return any(token in lowered for token in ["/give", "/tp", "/kill", "/gamemode", "/time", "/summon"])

    def _is_known_game_term(self, lowered: str) -> bool:
        terms = {"minecraft", "creeper", "netherite", "redstone", "valorant", "cs2", "csgo", "awp", "jett", "reyna"}
        return lowered in terms or any(term in lowered for term in terms)

    def _is_memory_query(self, lowered: str, memories: list[Any]) -> bool:
        if not memories:
            return False
        if "hatırla" in lowered or "hatirla" in lowered or "biliyorsun" in lowered or "ben kimim" in lowered:
            return True
        memory_keywords = [
            "adım ne", "benim adım", "ismim ne", "en sevdiğim", "favori", "kaç yaşındayım", "nerede yaşıyorum",
            "sevdigin", "sevdiğim", "favori rengim", "favori oyunum", "mesleğim",
        ]
        return any(keyword in lowered for keyword in memory_keywords)

    def _is_code_request(self, lowered: str) -> bool:
        code_keywords = ["kod yaz", "script yaz", "bot yaz", "uygulama yap", "html yaz", "css yaz", "python", "javascript", "java", "react", "api", "discord", "debug", "function"]
        return any(keyword in lowered for keyword in code_keywords)

    def _detect_domain(self, lowered: str) -> str:
        domains = {
            "minecraft": ["minecraft", "mc", "creeper", "nether", "redstone", "block"],
            "valorant": ["valorant", "valo", "jett", "reyna", "spike", "overrotate"],
            "tech": ["nvidia", "amd", "intel", "rtx", "ryzen", "gpu", "cpu", "windows", "apple", "samsung"],
        }
        for domain, keywords in domains.items():
            if any(keyword in lowered for keyword in keywords):
                return domain
        return "general"

    def _needs_web(self, lowered: str) -> bool:
        brands = ["nvidia", "amd", "intel", "apple", "samsung", "rtx", "ryzen", "iphone", "openai", "meta", "google", "microsoft", "tesla"]
        freshness = ["en son", "güncel", "yeni", "bugün", "bu ay", "fiyat", "kaç tl", "kur", "dolar", "euro", "altın", "patch", "release", "version", "tarif", "nasıl yapılır", "latest", "news", "price"]
        if any(brand in lowered for brand in brands) and ("?" in lowered or any(term in lowered for term in freshness)):
            return True
        return any(term in lowered for term in freshness)