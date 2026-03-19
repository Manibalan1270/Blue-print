import re
from typing import Dict

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class AIEngine:
    """Service class for semantic code analysis and lightweight impact scoring."""

    _SECRET_PATTERNS = [
        re.compile(r"\bsk_live_[A-Za-z0-9]{10,}\b"),
        re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    ]

    _LOGICAL_OPERATORS = ("if", "else", "while", "for", "switch", "case", "try", "except")

    def __init__(self) -> None:
        """Initialize the sentence embedding model on CPU for broad environment compatibility.

        Returns:
            None
        """
        self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    def mask_secrets(self, text: str) -> str:
        """Mask likely API keys and secrets from an input string.

        Args:
            text: Raw input text that may contain secret-like tokens.

        Returns:
            A sanitized string where detected secrets are replaced with '[REDACTED]'.
        """
        masked_text = text
        for pattern in self._SECRET_PATTERNS:
            masked_text = pattern.sub("[REDACTED]", masked_text)
        return masked_text

    def get_similarity(self, req_text: str, code_text: str) -> float:
        """Compute cosine similarity between requirement text and code-related text.

        Args:
            req_text: Requirement or ticket description text.
            code_text: Code, diff, or implementation text.

        Returns:
            Cosine similarity score in the range [0.0, 1.0].
        """
        cleaned_req = self._clean_text(req_text)
        cleaned_code = self._clean_text(code_text)

        vectors = self.model.encode([cleaned_req, cleaned_code], convert_to_numpy=True)
        score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
        return float(score)

    def calculate_impact(self, diff: str) -> Dict[str, object]:
        """Estimate complexity impact of a diff using lightweight control-flow heuristics.

        Args:
            diff: Unified diff or code snippet to inspect.

        Returns:
            A dictionary with:
            - complexity_score: Total count of logical/control-flow operators.
            - line_count: Total number of lines in the diff text.
            - impact_category: 'Low', 'Medium', or 'High' complexity tier.
        """
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

        return {
            "complexity_score": complexity_score,
            "line_count": line_count,
            "impact_category": impact_category,
        }

    def _clean_text(self, text: str) -> str:
        """Normalize and sanitize text before embedding generation.

        Args:
            text: Raw text to normalize.

        Returns:
            Sanitized, whitespace-normalized text safe for embedding.
        """
        sanitized = self.mask_secrets(text)
        return " ".join(sanitized.split()).strip()
