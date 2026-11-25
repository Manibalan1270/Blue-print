import re
from collections import Counter

from app.services.ai_engine import get_ai_engine


class InsightTranslator:
    """Rule-based translator from raw metrics to concise business-facing insights."""

    _AUTH_PATTERN = re.compile(r"\b(auth|login|jwt)\b", flags=re.IGNORECASE)
    _CORE_FILE_PATTERN = re.compile(
        r"\b(core|base|common|shared|utils|config|settings)\b", flags=re.IGNORECASE
    )
    _HIGH_SIMILARITY_THRESHOLD = 0.65
    _MEDIUM_SIMILARITY_THRESHOLD = 0.35
    _STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "with",
        "this",
        "these",
        "those",
        "reliability",
        "improve",
        "implementation",
    }

    def build_contribution_insight(self, diff_text: str, requirement_text: str) -> dict:
        """Return an evidence-backed insight packet with specific relevance details."""
        ai_engine = get_ai_engine()
        similarity_info = ai_engine.get_similarity(requirement_text, diff_text)
        impact_info = ai_engine.calculate_impact(diff_text)

        requirement_terms = self._extract_terms(requirement_text)
        code_terms = self._extract_terms(diff_text)
        overlap_terms = [term for term in requirement_terms if term in set(code_terms)][:6]

        function_names = self._extract_function_names(diff_text)
        changed_paths = self._extract_changed_paths(diff_text)

        focus_phrase = ", ".join(requirement_terms[:3]) if requirement_terms else "stated requirement objective"
        if function_names:
            code_signal = f"touched functions: {', '.join(function_names[:3])}"
        elif changed_paths:
            code_signal = f"changed files: {', '.join(changed_paths[:3])}"
        else:
            code_signal = "updated implementation logic in the provided diff"

        similarity = float(similarity_info["score"])
        complexity = int(impact_info["complexity_score"])
        impact_category = str(impact_info["impact_category"])
        contradiction_detected = bool(similarity_info.get("contradiction_detected", False))
        contradiction_detail = str(similarity_info.get("contradiction_detail", ""))

        if overlap_terms:
            overlap_phrase = f"matched requirement terms: {', '.join(overlap_terms)}"
        else:
            overlap_phrase = "few direct requirement terms were found in the code diff"

        if contradiction_detected:
            relevance_phrase = "misaligned due to opposite implementation intent"
        elif similarity >= 0.8:
            relevance_phrase = "highly relevant to the requirement"
        elif similarity >= self._HIGH_SIMILARITY_THRESHOLD:
            relevance_phrase = "meaningfully relevant to the requirement"
        elif similarity >= self._MEDIUM_SIMILARITY_THRESHOLD:
            relevance_phrase = "partially relevant and may need refinement"
        else:
            relevance_phrase = "weakly aligned with the requirement"

        contradiction_phrase = (
            f" Contradiction detected: {contradiction_detail}" if contradiction_detected else ""
        )

        summary = (
            f"Requirement focus: {focus_phrase}. "
            f"Code evidence: {code_signal}. "
            f"Relevance: {relevance_phrase} ({round(similarity * 100)}% similarity; {overlap_phrase}). "
            f"Effort signal: {impact_category} impact with complexity score {complexity}."
            f"{contradiction_phrase}"
        )

        relevance_reason = contradiction_detail if contradiction_detected else overlap_phrase

        return {
            "summary": summary,
            "requirement_focus_terms": requirement_terms[:6],
            "code_signals": {
                "functions": function_names[:6],
                "files": changed_paths[:6],
            },
            "overlap_terms": overlap_terms,
            "relevance_reason": relevance_reason,
            "contradiction_detected": contradiction_detected,
            "contradiction_detail": contradiction_detail,
        }

    def summarize_contribution(self, diff_text: str, requirement_text: str) -> str:
        """Return a concise summary string for backward compatibility."""
        return self.build_contribution_insight(diff_text, requirement_text)["summary"]

    def _extract_terms(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\-]{2,}", (text or "").lower())
        filtered = [token for token in tokens if token not in self._STOP_WORDS]
        return [term for term, _ in Counter(filtered).most_common(12)]

    def _extract_function_names(self, diff_text: str) -> list[str]:
        names = re.findall(r"(?:def|function|async\s+def)\s+([a-zA-Z_][a-zA-Z0-9_]*)", diff_text or "")
        deduped: list[str] = []
        for name in names:
            if name not in deduped:
                deduped.append(name)
        return deduped

    def _extract_changed_paths(self, diff_text: str) -> list[str]:
        matches = re.findall(r"^diff --git a/(.+?) b/", diff_text or "", flags=re.MULTILINE)
        deduped: list[str] = []
        for path in matches:
            if path not in deduped:
                deduped.append(path)
        return deduped
