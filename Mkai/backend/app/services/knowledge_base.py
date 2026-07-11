"""
Knowledge Base — Provider pattern ile genişletilebilir bilgi bankası.

Varsayılan olarak SQLite kullanır.  İleride PostgreSQL, vektör DB veya
JSON provider eklenebilir; sadece KnowledgeProvider ABC'sini implemente
etmek yeterlidir.
"""
from __future__ import annotations

import math
import os
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeEntry:
    domain: str
    term: str
    definition: str
    category: str = "general"
    language: str = "tr"

    def to_dict(self) -> dict[str, str]:
        return {
            "domain": self.domain,
            "term": self.term,
            "definition": self.definition,
            "category": self.category,
            "language": self.language,
        }


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------

class KnowledgeProvider(ABC):
    """Bilgi bankası veriye erişim katmanı."""

    @abstractmethod
    def lookup(self, term: str, *, domain: str = "general") -> KnowledgeEntry | None:
        """Tam terim eşleşmesi ile arama."""

    @abstractmethod
    def search(self, query: str, *, domain: str = "general", limit: int = 5) -> list[KnowledgeEntry]:
        """Kısmi eşleşme ile arama."""

    @abstractmethod
    def add_entry(self, entry: KnowledgeEntry) -> None:
        """Yeni kayıt ekle."""


# ---------------------------------------------------------------------------
# SQLite provider
# ---------------------------------------------------------------------------

_DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "knowledge.db"
)


class SQLiteKnowledgeProvider(KnowledgeProvider):
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or _DEFAULT_DB
        self._init_db()

    # -- schema ---------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain    TEXT    NOT NULL,
                    term      TEXT    NOT NULL COLLATE NOCASE,
                    definition TEXT   NOT NULL,
                    category  TEXT    DEFAULT 'general',
                    language  TEXT    DEFAULT 'tr',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(domain, term)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_domain_term "
                "ON knowledge(domain, term COLLATE NOCASE)"
            )
            count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            if count == 0:
                self._seed(conn)

    # -- seed data ------------------------------------------------------------

    def _seed(self, conn: sqlite3.Connection) -> None:
        """Başlangıç verilerini yükle."""
        rows: list[tuple[str, str, str, str]] = [
            # ── Valorant ──────────────────────────────────────────────
            ("valorant", "overrotate",
             "Takımın rakibin bir bölgeye girdiğini düşünerek gereğinden "
             "fazla oyuncuyla o bölgeye dönmesi ve bunun sonucunda diğer "
             "bölgenin boş kalmasıdır. Örneğin rakip A'ya fake atar, senin "
             "takımın 4 kişi A'ya döner, ama rakip B'ye girer. Buna "
             "overrotate denir.", "gaming_term"),
            ("valorant", "underrotate",
             "Overrotate'in tersi — takımın rakibin saldırdığı bölgeye "
             "yeterli sayıda oyuncu göndermemesi. Sonuç olarak o bölge "
             "kaybedilir.", "gaming_term"),
            ("valorant", "lurk",
             "Takımdan ayrılarak haritanın diğer tarafında sessizce bilgi "
             "toplama veya arkadan vurma stratejisi.", "gaming_term"),
            ("valorant", "default",
             "Raunun başında her oyuncunun haritanın belirli noktalarına "
             "dağılıp bilgi toplaması ve kontrol sağlaması.", "gaming_term"),
            ("valorant", "peek",
             "Köşeden kısa süreliğine çıkarak düşmanı görmeye çalışma "
             "hareketi.", "gaming_term"),
            ("valorant", "jiggle peek",
             "Köşeden çok hızlı bir şekilde çıkıp geri çekilerek düşmanın "
             "ateş etmesini tetikleme ve bilgi toplama hareketi.", "gaming_term"),
            ("valorant", "fake",
             "Bir bölgeye saldırı yapıyormuş gibi yapıp (ses, ability "
             "kullanma) asıl saldırıyı başka bölgeye yapma stratejisi.",
             "gaming_term"),
            ("valorant", "rotate",
             "Bir bölgeden diğerine geçiş yapma. Örneğin A'dan B'ye "
             "dönmek.", "gaming_term"),
            ("valorant", "retake",
             "Kaybedilen bir bölgeyi (site) geri almak için koordineli "
             "saldırı başlatma.", "gaming_term"),
            ("valorant", "one-tap",
             "Tek kurşunla headshot atarak düşmanı öldürme.", "gaming_term"),
            ("valorant", "ace",
             "Bir rauntta tek başına karşı takımın 5 oyuncusunu da "
             "öldürme.", "gaming_term"),
            ("valorant", "clutch",
             "Takımda tek kalan oyuncunun dezavantajlı durumda raundu "
             "kazanması.", "gaming_term"),
            ("valorant", "eco",
             "Para biriktirmek için ucuz silahlarla veya sadece pistol ile "
             "oynanan raunt.", "gaming_term"),
            ("valorant", "anti-eco",
             "Rakibin eco yaptığını bildiğinde shotgun veya SMG alarak "
             "avantaj elde etme stratejisi.", "gaming_term"),
            ("valorant", "trade",
             "Takım arkadaşın öldürüldüğünde hemen öldüren düşmanı "
             "öldürerek 1-1'e çevirme.", "gaming_term"),
            ("valorant", "bait",
             "Takım arkadaşını ileri göndererek düşmanın pozisyonunu "
             "öğrenme (genelde olumsuz bir terim).", "gaming_term"),
            ("valorant", "contact play",
             "İlk gördüğün düşmana hemen ateş açarak agresif oynama "
             "stratejisi.", "gaming_term"),
            ("valorant", "split push",
             "Takımın ikiye ayrılıp farklı yollardan aynı bölgeye "
             "girmesi.", "gaming_term"),
            ("valorant", "peek advantage",
             "Köşeden çıkan oyuncunun, köşeyi tutan oyuncuyu ağ gecikmesi "
             "nedeniyle daha erken görmesi avantajı. Peeker's advantage "
             "olarak da bilinir.", "gaming_term"),
            ("valorant", "crosshair placement",
             "Nişangahı her zaman kafa seviyesinde ve düşmanın çıkabileceği "
             "köşelerde tutma alışkanlığı.", "gaming_term"),

            # ── Minecraft ─────────────────────────────────────────────
            ("minecraft", "mob farm",
             "Otomatik olarak mob spawn edip öldüren ve drop toplayan "
             "yapı.", "gaming_term"),
            ("minecraft", "redstone",
             "Minecraft'taki elektrik/mantık devre sistemi. Kapılar, "
             "pistonlar, tuzaklar ve otomatik sistemler yapılabilir.",
             "gaming_term"),
            ("minecraft", "nether portal",
             "Obsidyen çerçeve ile oluşturulan Nether boyutuna geçiş "
             "kapısı. Minimum 4x5 obsidyen gerektirir.", "gaming_term"),
            ("minecraft", "enchanting",
             "Büyüleme masası veya anvil kullanarak eşyalara özel güçler "
             "ekleme sistemi.", "gaming_term"),
            ("minecraft", "elytra",
             "End şehrinden elde edilen uçma kanadı. Havai fişek ile "
             "birlikte kullanılarak süzülebilir.", "gaming_term"),
            ("minecraft", "iron golem farm",
             "Köylüleri kullanarak otomatik demir üretimi yapan farm "
             "yapısı.", "gaming_term"),
            ("minecraft", "beacon",
             "Nether yıldızı ile yapılan, çevresindeki oyunculara hız, "
             "güç gibi buff'lar veren blok.", "gaming_term"),
            ("minecraft", "shulker box",
             "End'den elde edilen, kırıldığında içindeki eşyaları koruyan "
             "taşınabilir sandık.", "gaming_term"),

            # ── CS2 ───────────────────────────────────────────────────
            ("cs2", "smoke",
             "Görüşü engelleyen duman bombası. Stratejik olarak geçişleri "
             "kapatmak veya defuse sırasında korunmak için kullanılır.",
             "gaming_term"),
            ("cs2", "flash",
             "Düşmanı geçici olarak kör eden flaş bombası.", "gaming_term"),
            ("cs2", "molotov",
             "Belirli bir alanı ateşe vererek düşmanın o bölgeden geçmesini "
             "engelleyen yanıcı bomba.", "gaming_term"),
            ("cs2", "wallbang",
             "Duvarın veya engelin arkasındaki düşmana kurşun geçirerek "
             "hasar verme.", "gaming_term"),
            ("cs2", "boost",
             "Bir oyuncunun diğerinin üzerine çıkarak normalde ulaşılamayan "
             "bir noktaya erişmesi.", "gaming_term"),
        ]

        conn.executemany(
            "INSERT OR IGNORE INTO knowledge (domain, term, definition, category) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )
        conn.commit()

    # -- queries --------------------------------------------------------------

    def lookup(self, term: str, *, domain: str = "general") -> KnowledgeEntry | None:
        with self._conn() as conn:
            # Önce domain-specific ara, sonra genel
            row = conn.execute(
                "SELECT * FROM knowledge "
                "WHERE LOWER(term) = LOWER(?) AND (domain = ? OR domain = 'general') "
                "ORDER BY CASE WHEN domain = ? THEN 0 ELSE 1 END "
                "LIMIT 1",
                (term, domain, domain),
            ).fetchone()
            if row:
                return KnowledgeEntry(
                    domain=row["domain"], term=row["term"],
                    definition=row["definition"], category=row["category"],
                    language=row["language"],
                )
        return None

    def search(self, query: str, *, domain: str = "general", limit: int = 5) -> list[KnowledgeEntry]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge "
                "WHERE (LOWER(term) LIKE ? OR LOWER(definition) LIKE ?) "
                "AND (domain = ? OR domain = 'general') "
                "ORDER BY CASE WHEN domain = ? THEN 0 ELSE 1 END "
                "LIMIT ?",
                (f"%{query.lower()}%", f"%{query.lower()}%", domain, domain, limit),
            ).fetchall()
            return [
                KnowledgeEntry(
                    domain=r["domain"], term=r["term"],
                    definition=r["definition"], category=r["category"],
                    language=r["language"],
                )
                for r in rows
            ]

    def add_entry(self, entry: KnowledgeEntry) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO knowledge "
                "(domain, term, definition, category, language) "
                "VALUES (?, ?, ?, ?, ?)",
                (entry.domain, entry.term, entry.definition,
                 entry.category, entry.language),
            )
            conn.commit()


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

# Basit matematik operasyonlarını güvenli şekilde hesapla
_SAFE_MATH_RE = re.compile(
    r"^[\d\s\+\-\*\/\.\(\)\%\^]+$"
)


class KnowledgeBase:
    """Ana bilgi bankası servisi."""

    def __init__(self, provider: KnowledgeProvider | None = None) -> None:
        self.provider = provider or SQLiteKnowledgeProvider()

    def lookup(self, term: str, *, domain: str = "general") -> KnowledgeEntry | None:
        return self.provider.lookup(term, domain=domain)

    def search(self, query: str, *, domain: str = "general", limit: int = 5) -> list[KnowledgeEntry]:
        return self.provider.search(query, domain=domain, limit=limit)

    def can_answer_directly(self, message: str) -> str | None:
        """
        LLM'e sormadan cevaplanabilecek sorular ve selamlaşmalar.
        Dönüş: cevap stringi veya None (LLM'e devret).
        """
        lowered = message.lower().strip()

        # 1. Selamlaşma Bypass (En hızlı cevap)
        greeting_ans = self._try_greeting(lowered)
        if greeting_ans is not None:
            return greeting_ans

        # 2. Basit matematik
        answer = self._try_math(lowered)
        if answer is not None:
            return answer

        # 3. Knowledge base'de tam eşleşme
        answer = self._try_knowledge_lookup(lowered)
        if answer is not None:
            return answer

        return None

    def _try_greeting(self, text: str) -> str | None:
        """Basit selamlaşmalara anında cevap ver."""
        greetings = {
            "merhaba": "Merhaba! Nasılsın? Bugün senin için ne yapabilirim?",
            "selam": "Selam! Nasılsın? Nasıl yardımcı olabilirim?",
            "sa": "Aleyküm selam! 😊 Nasılsın? Ne hakkında konuşalım?",
            "s.a": "Aleyküm selam! 😊 Nasılsın?",
            "naber": "İyidir, senden naber? Nasıl yardımcı olabilirim?",
            "günaydın": "Günaydın! Umarım harika bir gün geçirirsin. Sana nasıl yardım edebilirim?",
            "iyi geceler": "İyi geceler! Tatlı rüyalar. Yarın görüşürüz! 😊",
            "hey": "Hey! Ne var ne yok? Nasıl yardımcı olabilirim?",
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What's up?",
        }
        
        # Tam eşleşme veya noktalama işaretli eşleşme ("sa", "merhaba!", "selam...")
        cleaned = text.replace("!", "").replace(".", "").replace("?", "").strip()
        if cleaned in greetings:
            return greetings[cleaned]
            
        return None

    def _try_math(self, text: str) -> str | None:
        """Basit matematik ifadelerini hesapla."""
        # "2+2", "15*3", "100/4", "2^8" gibi
        cleaned = text.replace("kaç", "").replace("=", "").replace("?", "").strip()
        cleaned = cleaned.replace("^", "**").replace("x", "*")
        # "2 artı 3" gibi Türkçe ifadeler
        cleaned = cleaned.replace("artı", "+").replace("eksi", "-")
        cleaned = cleaned.replace("çarpı", "*").replace("bölü", "/")
        cleaned = cleaned.replace("plus", "+").replace("minus", "-")
        cleaned = cleaned.replace("times", "*").replace("divided by", "/")
        cleaned = cleaned.strip()

        if not cleaned or not _SAFE_MATH_RE.match(cleaned):
            return None
        try:
            result = eval(cleaned, {"__builtins__": {}}, {"math": math})  # noqa: S307
            if isinstance(result, float) and result == int(result):
                result = int(result)
            return str(result)
        except Exception:
            return None

    def _try_knowledge_lookup(self, text: str) -> str | None:
        """Bilinen terimleri bilgi bankasından bul."""
        # "overrotate nedir", "overrotate ne demek" gibi kalıplar
        patterns = [
            r"(?:valorant'?t?a?\s+)?(\w[\w\s\-]{1,30}?)\s+(?:nedir|ne\s+demek|ne\s+anlama?\s+gel)",
            r"(?:minecraft'?t?a?\s+)?(\w[\w\s\-]{1,30}?)\s+(?:nedir|ne\s+demek|ne\s+anlama?\s+gel)",
            r"(?:cs2'?d?e?\s+)?(\w[\w\s\-]{1,30}?)\s+(?:nedir|ne\s+demek|ne\s+anlama?\s+gel)",
            r"what\s+(?:is|does)\s+(\w[\w\s\-]{1,30}?)\s*(?:mean|\?|$)",
        ]

        # Domain tespiti
        domain = "general"
        if "valorant" in text:
            domain = "valorant"
        elif "minecraft" in text:
            domain = "minecraft"
        elif "cs2" in text or "counter" in text:
            domain = "cs2"

        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                term = m.group(1).strip()
                entry = self.provider.lookup(term, domain=domain)
                if entry:
                    return entry.definition

        return None

    def has_knowledge(self, term: str, *, domain: str = "general") -> bool:
        """Terim bilgi bankasında var mı?"""
        return self.provider.lookup(term, domain=domain) is not None
