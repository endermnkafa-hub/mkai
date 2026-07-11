"""Topic-aware conversation context manager for MKAI v4."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ConversationContext:
    topic: str
    subtopic: str
    references: list[str] = field(default_factory=list)
    resolved_message: str = ""
    turn_count: int = 0
    topic_changed: bool = False


_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "minecraft": ["minecraft", "mc", "creeper", "nether", "redstone", "block", "diamond", "netherite"],
    "valorant": ["valorant", "valo", "jett", "reyna", "spike", "overrotate", "agent"],
    "cs2": ["cs2", "csgo", "awp", "dust2", "counter strike"],
    "teknoloji": ["nvidia", "amd", "intel", "rtx", "ryzen", "gpu", "cpu", "apple", "samsung"],
    "programlama": ["python", "javascript", "java", "typescript", "rust", "go", "api", "kod", "function"],
}

_PRONOUNS = {"bu", "bunu", "bunun", "buna", "bundan", "o", "onu", "onun", "ona", "ondan", "şu", "şunu", "şunun", "şuna", "aynı", "aynısı"}


class ConversationManager:
    def analyze(self, message: str, *, history: list[dict[str, str]] | None = None) -> ConversationContext:
        history = history or []
        recent = history[-8:] if len(history) > 8 else history
        lowered = message.lower()

        current_topic = self._detect_topic(lowered)
        history_topic = self._detect_topic_from_history(recent)
        topic = current_topic if current_topic != "general" else history_topic

        topic_changed = False
        if current_topic != "general" and history_topic != "general" and current_topic != history_topic:
            topic_changed = True
        elif history_topic != "general" and current_topic == "general" and self._looks_like_new_topic(lowered):
            topic_changed = True

        if topic_changed:
            recent = []
            topic = current_topic

        references = self._extract_references(recent)
        subtopic = self._detect_subtopic(recent, lowered)
        resolved = self._resolve_references(message, references, subtopic, topic)

        return ConversationContext(
            topic=topic,
            subtopic=subtopic,
            references=references,
            resolved_message=resolved,
            turn_count=len(recent),
            topic_changed=topic_changed,
        )

    def _detect_topic(self, text: str) -> str:
        scores: dict[str, int] = {}
        for topic, keywords in _TOPIC_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score:
                scores[topic] = score
        if any(word in text for word in ["uzay", "big bang", "gezegen", "yıldız", "galaksi", "fizik", "bilim"]):
            scores["bilim"] = 5
        if not scores:
            return "general"
        return max(scores, key=scores.get)  # type: ignore[arg-type]

    def _detect_topic_from_history(self, history: list[dict[str, str]]) -> str:
        if not history:
            return "general"
        combined = " ".join(item.get("content", "").lower() for item in history[-4:])
        return self._detect_topic(combined)

    def _looks_like_new_topic(self, message: str) -> bool:
        lowered = message.lower()
        return "?" in message or any(word in lowered for word in ["nedir", "kimdir", "anlat", "nasıl", "ne demek"])

    def _extract_references(self, history: list[dict[str, str]]) -> list[str]:
        refs: list[str] = []
        seen: set[str] = set()
        for item in history:
            content = str(item.get("content", ""))
            for term in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", content):
                lowered = term.lower()
                if lowered not in seen and lowered not in {"ben", "sen", "bir", "the", "and", "for"}:
                    seen.add(lowered)
                    refs.append(term)
            for q in re.findall(r'["\']([^"\']{2,30})["\']', content):
                if q.lower() not in seen:
                    seen.add(q.lower())
                    refs.append(q)
        return refs[-8:]

    def _detect_subtopic(self, history: list[dict[str, str]], current: str) -> str:
        terms: set[str] = set()
        for item in reversed(history):
            if item.get("role") != "user":
                continue
            content = str(item.get("content", "")).lower()
            for match in re.finditer(r"\b([a-zçğıöşü0-9\s]{2,25})\s+(?:nedir|ne demek|nasıl)", content):
                terms.add(match.group(1).strip())
            for word in content.split():
                if len(word) >= 4 and word.isalpha():
                    terms.add(word)
            break
        return ", ".join(list(terms)[:3])

    def _resolve_references(self, message: str, references: list[str], subtopic: str, topic: str) -> str:
        lowered = message.lower()
        if not any(pronoun in lowered for pronoun in _PRONOUNS):
            return message
        if not references and not subtopic:
            return message
        last_ref = subtopic.split(",")[0].strip() if subtopic else references[-1]
        if not last_ref:
            return message
        resolved = message
        for pronoun in ["bunu", "buna", "bunun", "bundan", "onu", "ona", "onun", "ondan"]:
            if pronoun in lowered:
                resolved = re.sub(rf"\b{pronoun}\b", last_ref, resolved, flags=re.IGNORECASE, count=1)
                break
        if resolved == message:
            resolved = f"{message} [bağlam: {last_ref}, konu: {topic}]"
        return resolved
