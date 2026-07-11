"""Lightweight self-check for the v4 pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    retry_with_web: bool = False


_CHECK_ROUTES = {"web", "code"}


class SelfCheck:
    def should_check(self, route: str, *, enabled: bool = True) -> bool:
        return enabled and route in _CHECK_ROUTES

    async def check(self, *, question: str, answer: str, route: str, web_used: bool = False, provider_fn=None, enabled: bool = True) -> CheckResult:
        if not self.should_check(route, enabled=enabled):
            return CheckResult(passed=True)

        issues = self._heuristic_check(question, answer, route)
        if issues:
            return CheckResult(passed=False, issues=issues, retry_with_web=not web_used)
        return CheckResult(passed=True)

    def _heuristic_check(self, question: str, answer: str, route: str) -> list[str]:
        issues: list[str] = []
        answer_lower = answer.lower()
        question_lower = question.lower()

        if len(answer.strip()) < 8:
            issues.append("Cevap çok kısa")

        if any(token in answer_lower for token in ["özür dilerim", "i apologize", "as an ai", "yapay zeka"]):
            issues.append("Robotik ifade")

        if route == "code" and "```" not in answer and "def " not in answer and "function " not in answer:
            issues.append("Kod istendi ama cevap kod içermiyor")

        if any(token in answer_lower for token in ["minecraft", "creeper", "netherite", "valorant", "awp", "rtx"]):
            if not any(token in question_lower for token in ["minecraft", "creeper", "netherite", "valorant", "awp", "rtx"]):
                issues.append("Konu dışına çıkan içerik")

        if any(token in answer_lower for token in ["sanırım", "galiba", "emin değilim", "i think", "might be"]):
            issues.append("Belirsiz ifade")

        return issues
