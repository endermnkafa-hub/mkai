"""
Code Agent — Kod üretimi isteklerini analiz edip uygun prompt template'i seçer.

"Flappy Bird yaz" ile "Discord Bot yaz" aynı prompt'u kullanmaz.
Dil, zorluk ve proje tipine göre özelleştirilmiş talimatlar üretir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CodeContext:
    language: str        # "python", "javascript", "java", "html", "csharp"
    difficulty: str      # "basic", "intermediate", "advanced"
    project_type: str    # "game", "bot", "web", "script", "api", "cli", "general"
    needs_multiple_files: bool
    extra_instructions: str  # Proje tipine özel talimatlar


# ---------------------------------------------------------------------------
# Dil tespiti kuralları
# ---------------------------------------------------------------------------

_LANGUAGE_HINTS: dict[str, list[str]] = {
    "python": [
        "python", "py", "pygame", "flask", "django", "fastapi",
        "pip", "numpy", "pandas", "tkinter",
    ],
    "javascript": [
        "javascript", "js", "node", "nodejs", "react", "vue", "express",
        "npm", "next", "nextjs", "vite",
    ],
    "typescript": [
        "typescript", "ts", "angular", "deno",
    ],
    "java": [
        "java", "spring", "maven", "gradle", "jvm", "swing",
    ],
    "csharp": [
        "c#", "csharp", "unity", ".net", "dotnet", "wpf",
    ],
    "html": [
        "html", "css", "web sayfası", "website", "sayfa",
    ],
    "sql": [
        "sql", "mysql", "postgresql", "sqlite", "veritabanı", "database",
    ],
    "bash": [
        "bash", "shell", "terminal", "linux", "powershell", "bat",
    ],
    "rust": ["rust", "cargo"],
    "go": ["golang", "go lang"],
    "cpp": ["c++", "cpp"],
}

# Proje tipi tespiti
_PROJECT_HINTS: dict[str, list[str]] = {
    "game": [
        "oyun", "game", "flappy", "snake", "tetris", "pong", "arkanoid",
        "platformer", "shooter", "rpg", "pygame", "unity",
    ],
    "bot": [
        "bot", "discord", "telegram", "slack", "whatsapp", "chatbot",
    ],
    "web": [
        "web", "website", "site", "sayfa", "landing", "portfolio",
        "blog", "dashboard", "panel", "frontend",
    ],
    "api": [
        "api", "rest", "graphql", "endpoint", "backend", "server",
        "fastapi", "express", "flask", "django",
    ],
    "cli": [
        "cli", "komut satırı", "command line", "terminal", "script",
        "otomasyon", "automation",
    ],
    "script": [
        "script", "betik", "dosya", "hesapla", "dönüştür", "convert",
        "parse", "analiz",
    ],
}

# Proje tipine özel template'ler
_TEMPLATES: dict[str, str] = {
    "game": (
        "Tam çalışır, oynanabilir bir oyun yaz. Şunları içermeli:\n"
        "- Oyun döngüsü (game loop)\n"
        "- Skor sistemi\n"
        "- Oyun sonu / yeniden başlama\n"
        "- Temiz grafik/arayüz\n"
        "- Klavye/mouse kontrolleri\n"
        "Kodu tek dosyada, çalıştırılabilir şekilde yaz."
    ),
    "bot": (
        "Tam çalışır bir bot yaz. Şunları içermeli:\n"
        "- Token/API key konfigürasyonu (.env veya config)\n"
        "- Komut handler sistemi\n"
        "- Hata yönetimi (error handling)\n"
        "- Temel komutlar (help, ping, vb.)\n"
        "- Açıklayıcı yorumlar\n"
        "Token'ı hardcode etme, environment variable kullan."
    ),
    "web": (
        "Modern, responsive bir web sayfası/uygulaması yaz. Şunları içermeli:\n"
        "- Temiz, modern CSS tasarım\n"
        "- Responsive layout (mobil uyumlu)\n"
        "- Hover efektleri ve geçişler\n"
        "- Semantic HTML5\n"
        "- Accessibility (erişilebilirlik) temel kuralları"
    ),
    "api": (
        "Temiz, production-ready bir API yaz. Şunları içermeli:\n"
        "- Request validation\n"
        "- Error handling (uygun HTTP status kodları)\n"
        "- CORS ayarları\n"
        "- Temel CRUD endpoint'leri\n"
        "- Açıklayıcı docstring'ler"
    ),
    "cli": (
        "Kullanıcı dostu bir CLI uygulaması yaz. Şunları içermeli:\n"
        "- Argparse veya benzeri komut satırı ayrıştırma\n"
        "- --help desteği\n"
        "- Renkli çıktı (opsiyonel)\n"
        "- Hata mesajları\n"
        "- Kullanım örnekleri"
    ),
    "script": (
        "Temiz, anlaşılır bir script yaz. Şunları içermeli:\n"
        "- Açıklayıcı yorumlar\n"
        "- Hata yönetimi\n"
        "- if __name__ == '__main__' bloğu\n"
        "- Fonksiyonlara ayrılmış yapı"
    ),
    "general": (
        "Temiz, çalışır, iyi yorumlanmış kod yaz.\n"
        "- Best practice'lere uygun ol\n"
        "- Gereksiz karmaşıklıktan kaçın\n"
        "- Hata yönetimi ekle"
    ),
}


class CodeAgent:
    """Kod üretimi isteklerini analiz eder ve uygun prompt oluşturur."""

    def analyze(self, message: str) -> CodeContext:
        """Mesajdan dil, zorluk ve proje tipini çıkarır."""
        lowered = message.lower()

        language = self._detect_language(lowered)
        project_type = self._detect_project_type(lowered)
        difficulty = self._estimate_difficulty(lowered, project_type)

        # Dil belirlenemezse proje tipine göre tahmin
        if language == "python" and not any(h in lowered for h in _LANGUAGE_HINTS["python"]):
            if project_type == "web":
                language = "html"
            elif project_type == "game":
                language = "python"  # Pygame varsayılan
            elif project_type == "bot" and "discord" in lowered:
                language = "python"  # discord.py varsayılan

        needs_multiple = project_type in {"api", "web"} and difficulty == "advanced"

        return CodeContext(
            language=language,
            difficulty=difficulty,
            project_type=project_type,
            needs_multiple_files=needs_multiple,
            extra_instructions=_TEMPLATES.get(project_type, _TEMPLATES["general"]),
        )

    def build_code_prompt(self, context: CodeContext, message: str) -> str:
        """Kod tipine özel system prompt parçası oluşturur."""
        parts = [
            f"Programlama dili: {context.language}",
            f"Zorluk: {context.difficulty}",
            f"Proje tipi: {context.project_type}",
            "",
            "KURALLAR:",
            context.extra_instructions,
            "",
            "ÖNEMLİ:",
            "- Giriş cümlesi yazma, direkt kodla başla.",
            "- Kod eksiksiz ve çalıştırılabilir olsun.",
            "- Türkçe yorum ekle.",
        ]
        if context.needs_multiple_files:
            parts.append("- Birden fazla dosya gerekiyorsa her birini ayrı code block'ta yaz.")

        return "\n".join(parts)

    def _detect_language(self, text: str) -> str:
        """Mesajdan programlama dilini tespit et."""
        scores: dict[str, int] = {}
        for lang, hints in _LANGUAGE_HINTS.items():
            score = sum(1 for h in hints if h in text)
            if score > 0:
                scores[lang] = score
        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]
        return "python"  # Varsayılan

    def _detect_project_type(self, text: str) -> str:
        """Mesajdan proje tipini tespit et."""
        scores: dict[str, int] = {}
        for ptype, hints in _PROJECT_HINTS.items():
            score = sum(1 for h in hints if h in text)
            if score > 0:
                scores[ptype] = score
        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]
        return "general"

    def _estimate_difficulty(self, text: str, project_type: str) -> str:
        """Zorluk seviyesini tahmin et."""
        advanced_hints = [
            "karmaşık", "complex", "advanced", "full", "tam",
            "authentication", "database", "api", "real-time",
            "multiplayer", "çok oyunculu",
        ]
        basic_hints = [
            "basit", "simple", "basic", "kolay", "easy",
            "merhaba dünya", "hello world", "örnek",
        ]

        if any(h in text for h in advanced_hints):
            return "advanced"
        if any(h in text for h in basic_hints):
            return "basic"

        # Proje tipine göre varsayılan
        if project_type in {"game", "bot", "api"}:
            return "intermediate"
        return "basic"
