import re


class InsightTranslator:
    """Rule-based service that translates raw analysis data into professional summaries.

    Designed to be upgraded to an LLM-backed implementation without breaking its interface.
    """

    _AUTH_PATTERN = re.compile(r"\b(auth|login|jwt)\b", flags=re.IGNORECASE)
    _CORE_FILE_PATTERN = re.compile(
        r"\b(core|base|common|shared|utils|config|settings)\b", flags=re.IGNORECASE
    )

    _HIGH_SIMILARITY_THRESHOLD = 0.65

    def summarize_contribution(self, diff_text: str, requirement_text: str) -> str:
        """Generate a professional, jargon-free summary of a code contribution.

        Args:
            diff_text: Raw unified diff or code change content.
            requirement_text: Original ticket or requirement description.

        Returns:
            A concise, professional summary string suitable for executive reporting.
        """
        from ai_engine import AIEngine  # deferred import to keep this module lightweight

        similarity = AIEngine().get_similarity(requirement_text, diff_text)
        touches_auth = bool(self._AUTH_PATTERN.search(diff_text))
        touches_core = bool(self._CORE_FILE_PATTERN.search(diff_text))

        if touches_auth and similarity >= self._HIGH_SIMILARITY_THRESHOLD:
            return "Strengthened security protocols in the authentication gateway."

        if touches_core and similarity < self._HIGH_SIMILARITY_THRESHOLD:
            return "Architectural maintenance performed on core modules."

        if similarity >= self._HIGH_SIMILARITY_THRESHOLD:
            return "Delivered changes aligned with defined requirements."

        return "Exploratory improvements applied across the codebase."

    def get_impact_headline(self, complexity_score: int) -> str:
        """Return a professional headline describing engineering impact level.

        Args:
            complexity_score: Integer complexity score produced by AIEngine.calculate_impact.

        Returns:
            A short, professional headline string.
        """
        if complexity_score > 10:
            return "High-Impact Engineering"
        return "Standard Optimization"
