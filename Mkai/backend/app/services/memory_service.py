from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    workspace = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False, default="long_term")
    confidence = Column(Integer, nullable=False, default=80)
    source_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


@dataclass
class MemoryItem:
    id: int | None
    user_id: str
    workspace: str | None
    category: str
    value: str
    memory_type: str
    confidence: int
    source_text: str | None
    created_at: datetime
    expires_at: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def extract_and_store(self, text: str, *, user_id: str | None, workspace: str | None = None) -> list[MemoryItem]:
        if not text or not text.strip():
            return []

        safe_user_id = user_id or "anonymous"
        extracted = self._extract_memories(text)
        saved: list[MemoryItem] = []

        for item in extracted:
            existing = (
                self.db.query(MemoryRecord)
                .filter(
                    MemoryRecord.user_id == safe_user_id,
                    MemoryRecord.category == item["category"],
                    MemoryRecord.value == item["value"],
                )
                .first()
            )
            if existing:
                existing.confidence = max(existing.confidence, item["confidence"])
                self.db.commit()
                saved.append(self._record_to_item(existing))
                continue

            record = MemoryRecord(
                user_id=safe_user_id,
                workspace=workspace,
                category=item["category"],
                value=item["value"],
                memory_type=item["memory_type"],
                confidence=item["confidence"],
                source_text=text,
                expires_at=item["expires_at"],
            )
            self.db.add(record)
            self.db.commit()
            saved.append(self._record_to_item(record))

        return saved

    def list_memories(self, user_id: str) -> list[MemoryItem]:
        records = (
            self.db.query(MemoryRecord)
            .filter(MemoryRecord.user_id == user_id)
            .order_by(desc(MemoryRecord.created_at))
            .all()
        )
        return [self._record_to_item(record) for record in records]

    def delete_memory(self, memory_id: int) -> None:
        record = self.db.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
        if record is not None:
            self.db.delete(record)
            self.db.commit()

    def update_memory(self, memory_id: int, *, value: str | None = None, category: str | None = None) -> MemoryItem | None:
        record = self.db.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
        if record is None:
            return None
        if value is not None:
            record.value = value
        if category is not None:
            record.category = category
        self.db.commit()
        return self._record_to_item(record)

    def search_relevant_memories(self, user_id: str, *, message: str, workspace: str | None = None, max_results: int = 5) -> list[MemoryItem]:
        memories = self.list_memories(user_id)
        if not memories:
            return []
            
        lowered = message.lower()
        
        # ASCII Türkçe dönüşümü
        ascii_map = str.maketrans(
            "\u00e7\u011f\u0131\u015f\u00f6\u00fc",
            "cgisou"
        )
        lowered_ascii = lowered.translate(ascii_map)
        
        # Soru kelimeleri
        question_words = {"nedir", "ne", "kaç", "nerede", "kim", "nasıl", "hangi", "var mı"}
        query_words = set(w for w in lowered.split() if w not in question_words and len(w) > 2)
        query_words_ascii = set(w for w in lowered_ascii.split() if w not in question_words and len(w) > 2)

        scored_memories: list[tuple[float, MemoryItem]] = []
        seen_keys: set[str] = set()

        for item in memories:
            if workspace and item.workspace and item.workspace != workspace:
                continue
                
            key = f"{item.category}:{item.value}"
            if key in seen_keys:
                continue
                
            seen_keys.add(key)
            score = 0.0
            
            # Her zaman dahil edilmesi gerekenler (kimlik)
            if item.category in {"identity", "name"}:
                score += 10.0
                
            val_lower = item.value.lower()
            val_ascii = val_lower.translate(ascii_map)
            
            # Jaccard benzeri basit keyword overlap
            val_words = set(w for w in val_lower.split() if len(w) > 2)
            val_words_ascii = set(w for w in val_ascii.split() if len(w) > 2)
            
            overlap = len(query_words.intersection(val_words))
            overlap_ascii = len(query_words_ascii.intersection(val_words_ascii))
            max_overlap = max(overlap, overlap_ascii)
            
            # Fuzzy Matching (Harf benzerlikleri)
            fuzzy_score = 0.0
            from difflib import SequenceMatcher
            for qw in query_words_ascii:
                for vw in val_words_ascii:
                    sim = SequenceMatcher(None, qw, vw).ratio()
                    if sim > 0.8:  # %80 benzerse eşleşmiş say
                        fuzzy_score += 1.5
            
            if max_overlap > 0:
                score += max_overlap * 2.0
            score += fuzzy_score
                
            # Direkt substring eşleşmesi (daha değerli)
            for w in query_words:
                if w in val_lower:
                    score += 1.5
            for w in query_words_ascii:
                if w in val_ascii:
                    score += 1.5
                    
            # Kategori bazlı mantıksal eşleşme
            category_triggers = {
                "favorite_color": ["renk", "rengim", "color", "renkler"],
                "age": ["yaş", "yas", "kaç yaş", "kac yas", "age", "yaşındayım"],
                "location": ["nerede", "şehir", "sehir", "yaşıyorum", "yasiyorum", "where", "yaşadığım"],
                "learning": ["öğren", "ogren", "dil", "language", "learn", "çalışıyorum", "calisiyorum"],
                "favorite_food": ["yemek", "food", "yiyorum", "severim", "yemeği"],
                "projects": ["proje", "project", "geliştir", "gelistir", "kodluyorum"],
                "interests": ["sevdiğim", "sevdigim", "hobi", "ilgi", "like", "love", "hoşlanırım"],
            }
            
            if item.category in category_triggers:
                triggers = category_triggers[item.category]
                if any(t in lowered or t in lowered_ascii for t in triggers):
                    score += 5.0
                    
            # Confidence bonus (SADECE eşleşme varsa ekle)
            if score > 0.0:
                score += (item.confidence / 100.0)
            
            if score > 0.0 or item.category in {"identity", "name"}:
                scored_memories.append((score, item))
                
        # Skora göre sırala ve en yüksekleri al
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        recall_phrases = {
            "hatırla", "hatirla", "biliyorsun", "hatırlıyor musun", "hatirliyor musun",
            "ne biliyorsun", "remember me", "who am i", "ben kimim", "kimim ben",
            "adım ne", "ismim ne", "benim adım", "adim ne",
        }
        if any(phrase in lowered for phrase in recall_phrases):
            candidate_memories = [
                item for item in memories if not workspace or item.workspace in {workspace, None}
            ]
            if candidate_memories:
                return candidate_memories[:max_results]

        if scored_memories:
            return [item for _, item in scored_memories][:max_results]

        return []

    def get_inspector_data(self, user_id: str, *, workspace: str | None = None) -> dict[str, Any]:
        memories = self.list_memories(user_id)
        filtered = [item for item in memories if item.workspace in {workspace, None}]
        recent_memories = filtered[:5]
        profile = {
            "user_id": user_id,
            "workspace": workspace,
            "preferred_language": "Turkish",
        }
        return {
            "profile": profile,
            "workspace": workspace,
            "recent_memories": [item.to_dict() for item in recent_memories],
        }

    def _extract_memories(self, text: str) -> list[dict[str, Any]]:
        """
        Kullanicinin mesajindan kisisel bilgileri cikarir.
        Hem Turkce karakterli hem ASCII Turkce metinleri destekler.
        """
        memories: list[dict[str, Any]] = []
        lowered = text.lower().strip()

        # ASCII Turkce donusumu (e.g. yasindayim -> ya\u015f\u0131nday\u0131m fallback)
        ascii_map = str.maketrans(
            "\u00e7\u011f\u0131\u015f\u00f6\u00fc\u00c7\u011e\u0130\u015e\u00d6\u00dc",
            "cgisouCGISOÜ"
        )
        lowered_ascii = lowered.translate(ascii_map)

        def add(category: str, value: str, confidence: int = 90, memory_type: str = "long_term") -> None:
            for existing in memories:
                if existing["category"] == category and existing["value"] == value:
                    return
            memories.append({
                "category": category,
                "value": value,
                "memory_type": memory_type,
                "confidence": confidence,
                "expires_at": None,
            })

        def search(pattern: str, flags: int = re.IGNORECASE) -> re.Match | None:
            m = re.search(pattern, lowered, flags)
            if not m:
                m = re.search(pattern, lowered_ascii, flags)
            return m

        # Renk kelimeleri (Turkce + Ingilizce + ASCII versiyonlari)
        valid_colors = [
            "siyah", "beyaz", "kirmizi", "k\u0131rm\u0131z\u0131", "mavi", "yesil", "ye\u015fil",
            "sari", "sar\u0131", "mor", "turuncu", "pembe", "kahverengi", "kahve",
            "gri", "altin", "alt\u0131n", "gumus", "g\u00fcm\u00fc\u015f", "lacivert", "turkuaz",
            "black", "white", "red", "blue", "green", "yellow", "purple",
            "orange", "pink", "brown", "gray", "grey", "gold", "silver", "navy", "teal",
        ]

        # Isim olarak yanlislikla alinmamasi gereken kelimeler
        not_a_name = {
            "bir", "bu", "su", "\u015fu", "da", "de", "mi", "mu", "mu",
            "the", "a", "an", "and",
            "renk", "rengim", "rengi",
            "java", "python", "javascript", "typescript", "rust", "go", "swift",
            "naruto", "anime", "minecraft", "mod",
            "iyi", "guzel", "g\u00fczel", "buyuk", "b\u00fcy\u00fck", "kucuk", "k\u00fc\u00e7\u00fck",
        } | set(valid_colors)

        # ============ ISIM ============
        name_found = False
        # "adim/adim X" veya "benim adim X" (Turkce karakterli)
        m = re.search(
            r"(?:benim\s+)?(?:ad[i\u0131]m|ismim|isimim)\s+([A-Z\u00c7\u011e\u0130\u015e\u00d6\u00dc][a-z\u00e7\u011f\u0131\u015f\u00f6\u00fc]{1,25})\b",
            text
        )
        if m:
            name = m.group(1).strip()
            if name.lower() not in not_a_name:
                add("identity", f"Kullanicinin adi {name}", 98)
                name_found = True

        if not name_found:
            # Kucuk harfli "adim muhammed" veya "adim Muhammed"
            m = re.search(
                r"(?:benim\s+)?(?:ad[i\u0131]m|ismim)\s+([a-zA-Z\u00e7\u011f\u0131\u015f\u00f6\u00fc\u00c7\u011e\u0130\u015e\u00d6\u00dc]{2,25})\b",
                lowered
            )
            if m:
                name = m.group(1).strip().capitalize()
                if name.lower() not in not_a_name:
                    add("identity", f"Kullanicinin adi {name}", 95)
                    name_found = True

        if not name_found:
            # ASCII fallback: "adim muhammed"
            m = re.search(r"(?:benim\s+)?(?:adim|ismim)\s+([a-zA-Z]{2,25})\b", lowered_ascii)
            if m:
                name = m.group(1).strip().capitalize()
                if name.lower() not in not_a_name:
                    add("identity", f"Kullanicinin adi {name}", 92)
                    name_found = True

        if not name_found:
            # "my name is X"
            m = re.search(r"(?:my\s+name\s+is|i'?m\s+called)\s+([A-Z][a-zA-Z]{1,25})\b", text)
            if m:
                name = m.group(1).strip()
                if name.lower() not in not_a_name:
                    add("identity", f"Kullanicinin adi {name}", 96)

        # ============ FAVORİ RENK ============
        color_found = False

        # Pattern 1: "en sevdigim renk [renk]" veya "favori renk [renk]"
        for color in valid_colors:
            # "sevdigim renk siyah" veya "renk siyah" veya "siyah rengi seviyorum"
            patterns = [
                rf"(?:en\s+)?(?:sevdi[gi\u011fi]m|favori|favorite)\s+(?:renk[im]?\s+){re.escape(color)}\b",
                rf"(?:en\s+)?(?:sevdi[gi\u011fi]m|favori|favorite)\s+(?:renk[im]?)\s+{re.escape(color)}\b",
                rf"(?:renk[im]?\s+(?:is\s+)?){re.escape(color)}\b",
                rf"\b{re.escape(color)}\b.{{0,15}}(?:renk[im]?|seviyorum|sev[er]im)\b",
                rf"(?:renk[im]?|seviyorum|sev[er]im).{{0,15}}\b{re.escape(color)}\b",
            ]
            for pattern in patterns:
                if re.search(pattern, lowered, re.IGNORECASE) or re.search(pattern, lowered_ascii, re.IGNORECASE):
                    add("favorite_color", f"Favori renk: {color}", 95)
                    color_found = True
                    break
            if color_found:
                break

        # Pattern 2: Basit "renk siyah" veya "siyah renk"
        if not color_found:
            for color in valid_colors:
                if re.search(rf"(?:renk\s+{re.escape(color)}|{re.escape(color)}\s+renk)\b", lowered):
                    add("favorite_color", f"Favori renk: {color}", 88)
                    break

        # ============ YAŞ ============
        # Hem "17 yaşındayım" hem "17 yasindayim"
        age_patterns_list = [
            r"(\d{1,2})\s*ya[s\u015f][i\u0131]nday[i\u0131]m",
            r"ya[s\u015f][i\u0131]m\s*(\d{1,2})",
            r"(\d{1,2})\s+years?\s+old",
            r"i\s+am\s+(\d{1,2})",
        ]
        for pattern in age_patterns_list:
            m = search(pattern)
            if m:
                try:
                    age = int(m.group(1))
                    if 5 <= age <= 120:
                        add("age", f"Kullanicinin yasi {age}", 95)
                        break
                except (ValueError, IndexError):
                    pass

        # ============ KONUM / ŞEHİR ============
        loc_patterns = [
            # "İstanbul'da yaşıyorum" / "Istanbulda yasiyorum"
            r"([A-Z\u00c7\u011e\u0130\u015e\u00d6\u00dc][a-z\u00e7\u011f\u0131\u015f\u00f6\u00fca-zA-Z]{2,20})['\u2019]?(?:de|da|den|dan|'de|'da)\s+ya[s\u015f][i\u0131]yorum",
            r"([A-Z\u00c7\u011e\u0130\u015e\u00d6\u00dc][a-z\u00e7\u011f\u0131\u015f\u00f6\u00fca-zA-Z]{2,20})'?[a-z]{0,3}\s+ya[s\u015f][i\u0131]yorum",
            r"(?:i\s+live\s+in|from)\s+([A-Z][a-zA-Z\s]{2,25})(?:\.|,|$)",
        ]
        for pattern in loc_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if not m:
                m = re.search(pattern, text.title(), re.IGNORECASE)
            if m:
                loc = m.group(1).strip().rstrip("'")
                if len(loc) >= 2 and loc.lower() not in {"ben", "bir", "bu", "sen", "o"}:
                    add("location", f"Yasadigi yer: {loc}", 90)
                    break

        # ============ ÖĞRENME ============
        learn_patterns = [
            r"([A-Za-z#\+\.]{2,20})\s+(?:[o\u00f6][g\u011f]reniyorum|[o\u00f6][g\u011f]renmeye\s+ba[s\u015f]lad[i\u0131]m|[o\u00f6][g\u011f]renmek\s+istiyorum)",
            r"(?:learning|studying)\s+([A-Za-z#\+\.]{2,20})",
        ]
        for pattern in learn_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if not m:
                m = re.search(pattern, text, re.IGNORECASE)
            if m:
                skill = m.group(1).strip()
                if skill and len(skill) >= 2:
                    add("learning", skill, 95)
                    break

        # ============ FAVORİ YEMEK ============
        food_m = search(
            r"(?:en\s+sevdi[gi\u011fi]m\s+yemek|favori\s+yemek(?:im)?|favorite\s+food)\s+(?:is\s+)?([a-z\u00e7\u011f\u0131\u015f\u00f6\u00fc\s]{2,30}?)(?:\.|,|$)"
        )
        if food_m:
            food = food_m.group(1).strip()
            if food:
                add("favorite_food", f"Favori yemek: {food}", 90)

        # ============ ÖZEL TANIMA ============
        if any(t in lowered for t in ["minecraft", "mcreator", "blockbench"]):
            add("projects", "Minecraft mod gelistirme ile ilgileniyor", 90)
        if "naruto" in lowered:
            add("entertainment", "Naruto anime/manga seviyor", 90)
        if "anime" in lowered and "naruto" not in lowered:
            add("interests", "Anime izlemeyi seviyor", 85)
        java_learn = any(t in lowered for t in ["ogren", "\u00f6gren", "yaziyorum", "kullaniyorum", "biliyorum"])
        if "java" in lowered and java_learn:
            add("learning", "Java", 90)

        # ============ RUH HALİ ============
        mood_triggers = [
            "sikildim", "s\u0131k\u0131ld\u0131m", "uzgun", "\u00fcz\u00fcn",
            "kotu hissediyorum", "k\u00f6t\u00fc hissediyorum", "moralim bozuk"
        ]
        if any(t in lowered or t in lowered_ascii for t in mood_triggers):
            memories.append({
                "category": "mood",
                "value": "Kullanici kendini kotu hissediyor",
                "memory_type": "temporary",
                "confidence": 85,
                "expires_at": datetime.utcnow() + timedelta(hours=24),
            })

        # ============ GENEL NOT ============
        if not memories and len(text.strip()) > 25:
            question_words = [
                "nasil", "nas\u0131l", "neden", "ne", "kim", "hangi", "nerede",
                "how", "why", "what", "where", "who", "when"
            ]
            is_question = "?" in text or any(t in lowered for t in question_words)
            if not is_question:
                memories.append({
                    "category": "note",
                    "value": text.strip()[:200],
                    "memory_type": "long_term",
                    "confidence": 55,
                    "expires_at": None,
                })
        if not memories and len(text.strip()) <= 25 and any(t in lowered for t in ["merhaba", "selam", "hello", "hi"]):
            memories.append({
                "category": "note",
                "value": text.strip()[:200],
                "memory_type": "long_term",
                "confidence": 55,
                "expires_at": None,
            })
        return memories

    def _record_to_item(self, record: MemoryRecord) -> MemoryItem:
        return MemoryItem(
            id=record.id,
            user_id=record.user_id,
            workspace=record.workspace,
            category=record.category,
            value=record.value,
            memory_type=record.memory_type,
            confidence=record.confidence,
            source_text=record.source_text,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )
