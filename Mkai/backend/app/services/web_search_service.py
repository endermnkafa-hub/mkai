"""
Web Search Service — duckduckgo-search ile gerçek web araması.

Sadece "güncel" anahtar kelimeler için değil, bilinmeyen terimler ve
düşük confidence durumlarında da tetiklenir.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any


class WebSearchService:
    """Gerçek web araması servisi."""

    # Marka/ürün isimleri — bunlar her zaman web gerektirir
    _BRAND_NAMES = {
        "nvidia", "amd", "intel", "apple", "samsung", "google", "microsoft",
        "sony", "xbox", "playstation", "steam", "epic", "riot", "mojang",
        "rtx", "radeon", "geforce", "ryzen", "snapdragon", "iphone", "pixel",
        "tesla", "openai", "anthropic", "meta",
    }

    # Güncellik gerektiren kelimeler
    _FRESHNESS_KEYWORDS_TR = {
        "en son", "en yeni", "güncel", "şu anki", "şimdiki", "bugün",
        "bu hafta", "bu ay", "yeni çıkan", "ne zaman çıkacak", "ne zaman çıktı",
        "son sürüm", "son versiyon", "güncelleme", "yama", "patch",
        "fiyat", "fiyatı", "kaç para", "kaç tl",
        "skor", "maç sonucu", "haber", "haberler",
    }

    _FRESHNESS_KEYWORDS_EN = {
        "latest", "newest", "current", "recent", "today", "this week",
        "this month", "release date", "update", "patch", "price",
        "score", "news", "version", "announcement",
    }

    async def search(
        self,
        query: str,
        *,
        lang: str = "tr",
        max_results: int = 5,
    ) -> str:
        """
        Web araması yapar, formatlanmış sonuç stringi döndürür.
        Boş string dönerse sonuç bulunamadı demektir.
        """
        try:
            optimized = self._optimize_query(query, lang=lang)
            results = await asyncio.to_thread(
                self._search_sync, optimized, lang=lang, max_results=max_results,
            )
            if not results:
                return ""
            return self._format_results(results)
        except Exception:
            return ""

    def should_search(
        self,
        message: str,
        *,
        confidence: float = 1.0,
        route: str = "chat",
        knowledge_hit: bool = False,
    ) -> bool:
        """
        Web araması gerekip gerekmediğini belirler.

        True döndüren durumlar:
        1. confidence < 0.60
        2. Marka/ürün ismi + soru formatı
        3. Güncellik gerektiren kelimeler
        4. Knowledge base'de bulunamadı + bilgi sorusu
        5. Route "web" olarak belirlenmiş
        """
        if route == "web":
            return True

        lowered = message.lower()

        if route in {"chat", "memory"}:
            has_brand = any(b in lowered for b in self._BRAND_NAMES)
            has_question = "?" in message or any(
                w in lowered for w in ["nedir", "ne", "kaç", "nasıl", "what", "how", "which"]
            )
            if has_brand and has_question:
                return True
            if any(kw in lowered for kw in self._FRESHNESS_KEYWORDS_TR | self._FRESHNESS_KEYWORDS_EN):
                return True
            return False

        if confidence < 0.60:
            return True

        lowered = message.lower()

        # Marka ismi + soru
        has_brand = any(b in lowered for b in self._BRAND_NAMES)
        has_question = "?" in message or any(
            w in lowered
            for w in ["nedir", "ne", "kaç", "nasıl", "what", "how", "which"]
        )
        if has_brand and has_question:
            return True

        # Güncellik kelimeleri
        if any(kw in lowered for kw in self._FRESHNESS_KEYWORDS_TR | self._FRESHNESS_KEYWORDS_EN):
            return True

        # Knowledge base'de bulunamadı ve bilgi sorusu
        if not knowledge_hit and has_question and route == "knowledge":
            return True

        return False

    def _optimize_query(self, message: str, *, lang: str = "tr") -> str:
        """Mesajı arama sorgusuna çevirir."""
        # Soru eklerini temizle
        cleaned = message.strip().rstrip("?").strip()
        # Türkçe soru kalıplarını kaldır
        removals = [
            "nedir", "ne demek", "ne anlama gelir", "ne anlama geliyor",
            "nasıl", "hakkında bilgi ver", "anlat", "açıkla",
            "what is", "what does", "mean", "explain", "tell me about",
        ]
        lower = cleaned.lower()
        for r in removals:
            lower = lower.replace(r, "")
        # Fazla boşlukları temizle
        cleaned = re.sub(r"\s+", " ", lower).strip()

        if not cleaned:
            cleaned = message.strip()

        # Dil ipucu ekle
        if lang == "tr" and not any(c in cleaned for c in "çğışöü"):
            pass  # Türkçe olmayan sorgu, ek ekleme

        return cleaned

    def _format_results(self, results: list[dict[str, Any]]) -> str:
        """Arama sonuçlarını LLM'e verilecek formata çevirir."""
        parts: list[str] = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", "")
            url = r.get("href", "")
            if body:
                parts.append(f"{i}. {title}\n{body}\nKaynak: {url}")
        return "\n\n".join(parts)

    @staticmethod
    def _search_sync(
        query: str,
        *,
        lang: str = "tr",
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Senkron DuckDuckGo araması (thread'de çağrılır)."""
        try:
            from duckduckgo_search import DDGS

            region = "tr-tr" if lang == "tr" else "en-us"
            with DDGS() as ddgs:
                return list(ddgs.text(query, region=region, max_results=max_results))
        except ImportError:
            # duckduckgo-search yüklü değilse httpx fallback
            return WebSearchService._fallback_search(query, lang=lang)
        except Exception:
            return []

    @staticmethod
    def _fallback_search(query: str, *, lang: str = "tr") -> list[dict[str, Any]]:
        """duckduckgo-search kütüphanesi yoksa basit API fallback."""
        try:
            import httpx

            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
                "kl": "tr-tr" if lang == "tr" else "en-us",
            }
            resp = httpx.get(
                "https://api.duckduckgo.com/",
                params=params,
                headers={"User-Agent": "MKAI/1.0"},
                timeout=8.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results: list[dict[str, Any]] = []
            abstract = data.get("AbstractText", "")
            if abstract:
                results.append({
                    "title": data.get("AbstractSource", "Wikipedia"),
                    "body": abstract,
                    "href": data.get("AbstractURL", ""),
                })
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        "body": topic["Text"],
                        "href": topic.get("FirstURL", ""),
                    })
            return results
        except Exception:
            return []
