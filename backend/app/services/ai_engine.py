import re
from functools import lru_cache
from typing import Dict

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class AIEngine:
    """Service class for semantic similarity and impact scoring."""

    _LOGICAL_OPERATORS = ("if", "else", "while", "for", "switch", "case", "try", "except")

    _SECRET_PATTERNS = [
        re.compile(r"\bsk_live_[A-Za-z0-9]{10,}\b"),
        re.compile(r"\bsk_test_[A-Za-z0-9]{10,}\b"),
        re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    ]

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
        "all",
        "every",
    }

    _NEGATIVE_INTENT_TERMS = {
        "disable",
        "disabled",
        "block",
        "blocked",
        "reject",
        "rejected",
        "deny",
        "denied",
        "forbid",
        "forbidden",
        "prevent",
        "prevented",
        "remove",
        "removed",
    }

    _POSITIVE_INTENT_TERMS = {
        "allow",
        "allowed",
        "grant",
        "granted",
        "enable",
        "enabled",
        "accept",
        "accepted",
        "permit",
        "permitted",
        "approve",
        "approved",
    }

    _AUTH_DOMAIN_TERMS = {
        "auth",
        "authentication",
        "login",
        "jwt",
        "token",
        "refresh",
        "issuer",
        "audience",
        "expiry",
        "expired",
        "lock",
        "account",
        "session",
    }

    _PERMISSIVE_CODE_PATTERNS = [
        re.compile(r"\breturn\s+true\b", flags=re.IGNORECASE),
        re.compile(r"\bgrant[_\s]?access\b", flags=re.IGNORECASE),
        re.compile(r"\ballow[_\s]?(login|access|auth|authentication)\b", flags=re.IGNORECASE),
        re.compile(r"\benable[_\s]?(login|access|auth|authentication)\b", flags=re.IGNORECASE),
    ]

    _RESTRICTIVE_CODE_PATTERNS = [
        re.compile(r"\breturn\s+false\b", flags=re.IGNORECASE),
        re.compile(r"\b(block|reject|deny|forbid|prevent|disable)\b", flags=re.IGNORECASE),
    ]

    def __init__(self) -> None:
        """Initialize the embedding model on CPU for portability."""
        self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    def mask_secrets(self, text: str) -> str:
        """Redact common API key formats from text before analysis."""
        if not text:
            return ""
        masked = text
        for pattern in self._SECRET_PATTERNS:
            masked = pattern.sub("[REDACTED]", masked)
        return masked

    def get_similarity(self, req_text: str, code_text: str) -> Dict[str, object]:
        """Return semantic mapping score with an explainable rationale."""
        if not req_text or not code_text:
            return {
                "score": 0.0,
                "explanation": "One or both inputs were empty, so semantic alignment is reported as zero.",
                "normalized_requirement_length": 0,
                "normalized_code_length": 0,
                "semantic_score": 0.0,
                "keyword_overlap": 0.0,
                "contradiction_detected": False,
                "contradiction_detail": "No contradiction check performed due to empty input.",
            }

        req = self._clean_text(req_text)
        code = self._clean_text(code_text)
        if not req or not code:
            return {
                "score": 0.0,
                "explanation": "Input normalization removed analyzable content, resulting in zero alignment.",
                "normalized_requirement_length": len(req),
                "normalized_code_length": len(code),
                "semantic_score": 0.0,
                "keyword_overlap": 0.0,
                "contradiction_detected": False,
                "contradiction_detail": "No contradiction check performed after normalization.",
            }

        vectors = self.model.encode([req, code], convert_to_numpy=True)
        semantic_score = float(cosine_similarity([vectors[0]], [vectors[1]])[0][0])

        req_terms = set(self._extract_terms(req))
        code_terms = set(self._extract_terms(code))
        overlap_terms = req_terms.intersection(code_terms)
        keyword_overlap = len(overlap_terms) / max(1, len(req_terms))

        contradiction_detected, contradiction_detail = self._detect_intent_conflict(req_terms, code_terms, code)
        contradiction_penalty = 1.0 if contradiction_detected else 0.0

        req_auth_terms = req_terms.intersection(self._AUTH_DOMAIN_TERMS)
        code_auth_terms = code_terms.intersection(self._AUTH_DOMAIN_TERMS)
        shared_auth_terms = req_auth_terms.intersection(code_auth_terms)
        auth_overlap_ratio = len(shared_auth_terms) / max(1, len(req_auth_terms))

        domain_boost = 0.0
        if not contradiction_detected and req_auth_terms and code_auth_terms:
            domain_boost = min(0.20, 0.40 * auth_overlap_ratio)

        # Blend semantic distance with lexical overlap, then penalize opposite intent.
        blended_score = (
            (0.75 * semantic_score)
            + (0.30 * keyword_overlap)
            + domain_boost
            - (0.45 * contradiction_penalty)
        )
        if contradiction_detected:
            blended_score = min(blended_score, 0.20)

        score = max(0.0, min(1.0, blended_score))

        if score >= 0.8:
            explanation = "Requirement intent is strongly reflected in implementation changes."
        elif score >= 0.6:
            explanation = "Implementation appears partially aligned with the requirement intent."
        elif score >= 0.35:
            explanation = "Implementation shows limited requirement alignment and may need review."
        else:
            explanation = "Implementation diverges from requirement intent based on semantic distance."

        if contradiction_detected:
            explanation = (
                "Intent conflict detected between requirement and implementation actions; "
                f"alignment score was capped. {contradiction_detail}"
            )

        return {
            "score": score,
            "explanation": explanation,
            "normalized_requirement_length": len(req),
            "normalized_code_length": len(code),
            "semantic_score": round(semantic_score, 4),
            "keyword_overlap": round(keyword_overlap, 4),
            "contradiction_detected": contradiction_detected,
            "contradiction_detail": contradiction_detail,
        }

    def calculate_impact(self, diff: str) -> Dict[str, object]:
        """Estimate impact from operator density and line count with explanation."""
        normalized = self.mask_secrets(diff)

        complexity_score = 0
        for operator in self._LOGICAL_OPERATORS:
            complexity_score += len(re.findall(rf"\b{re.escape(operator)}\b", normalized, flags=re.IGNORECASE))

        line_count = len(normalized.splitlines())

        if complexity_score <= 3:
            impact_category = "Low"
        elif complexity_score <= 8:
            impact_category = "Medium"
        else:
            impact_category = "High"

        if complexity_score <= 3:
            explanation = "Few control-flow branches were detected; implementation complexity appears contained."
        elif complexity_score <= 8:
            explanation = "Moderate branching indicates meaningful effort with manageable implementation risk."
        else:
            explanation = "High branching density indicates elevated functional complexity and integration effort."

        return {
            "complexity_score": complexity_score,
            "line_count": line_count,
            "impact_category": impact_category,
            "explanation": explanation,
        }

    def _clean_text(self, text: str) -> str:
        """Normalize and sanitize free-form text for embedding generation."""
        sanitized = self.mask_secrets(text)
        return " ".join(sanitized.split()).strip()

    def _extract_terms(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\-]{2,}", (text or "").lower())
        expanded: list[str] = []
        for token in tokens:
            if token not in self._STOP_WORDS:
                expanded.append(token)
            for part in re.split(r"[_\-]+", token):
                if len(part) >= 3 and part not in self._STOP_WORDS:
                    expanded.append(part)
        return expanded

    def _detect_intent_conflict(self, req_terms: set[str], code_terms: set[str], code_text: str) -> tuple[bool, str]:
        req_negative = sorted(req_terms.intersection(self._NEGATIVE_INTENT_TERMS))
        req_positive = sorted(req_terms.intersection(self._POSITIVE_INTENT_TERMS))
        code_negative = sorted(code_terms.intersection(self._NEGATIVE_INTENT_TERMS))
        code_positive = sorted(code_terms.intersection(self._POSITIVE_INTENT_TERMS))

        code_has_permissive_pattern = any(pattern.search(code_text) for pattern in self._PERMISSIVE_CODE_PATTERNS)
        code_has_restrictive_pattern = any(pattern.search(code_text) for pattern in self._RESTRICTIVE_CODE_PATTERNS)

        req_negative_vs_code_positive = bool(req_negative and (code_positive or code_has_permissive_pattern))
        req_positive_vs_code_negative = bool(req_positive and (code_negative or code_has_restrictive_pattern))

        if req_negative_vs_code_positive:
            return (
                True,
                f"Requirement requests restrictive actions ({', '.join(req_negative)}), "
                f"but code uses permissive actions ({', '.join(code_positive) if code_positive else 'pattern-based permissive behavior'}).",
            )

        if req_positive_vs_code_negative:
            return (
                True,
                f"Requirement requests permissive actions ({', '.join(req_positive)}), "
                f"but code uses restrictive actions ({', '.join(code_negative) if code_negative else 'pattern-based restrictive behavior'}).",
            )

        return False, "No direct intent contradiction detected from action terms."


@lru_cache(maxsize=1)
def get_ai_engine() -> "AIEngine":
    """Shared AIEngine. Loading the embedding model takes seconds and ~100MB of
    memory, so it is created once per process instead of on every request."""
    return AIEngine()
