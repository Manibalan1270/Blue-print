from collections import Counter
from datetime import datetime, timezone


class RiskEngine:
    """Data science service for analysing team health, burnout risk, and code hotspots."""

    _OWNERSHIP_THRESHOLD = 0.70
    _BURNOUT_COMMIT_DAYS_PER_WEEK = 7
    _BURNOUT_SUSTAINED_WEEKS = 3
    _CRITICAL_COMPLEXITY = 15
    _CRITICAL_BUG_FREQUENCY = 5
    _ELEVATED_COMPLEXITY = 10

    def calculate_bus_factor(self, commit_data: list[dict]) -> int:
        """Calculate the bus factor for a module based on commit ownership distribution.

        Args:
            commit_data: List of commit records, each containing at least an 'author'
                         key and optionally a 'lines_changed' key.
                         Example: [{"author": "alice", "lines_changed": 200}, ...]

        Returns:
            Bus factor as an integer. Returns 1 when a single author owns more than
            70% of the total code changes, indicating critical single-point-of-failure risk.
        """
        if not commit_data:
            return 0

        change_counts: Counter = Counter()
        for commit in commit_data:
            author = commit.get("author", "unknown")
            lines = int(commit.get("lines_changed", 1))
            change_counts[author] += lines

        total = sum(change_counts.values())
        if total == 0:
            return 0

        top_author, top_count = change_counts.most_common(1)[0]
        if top_count / total > self._OWNERSHIP_THRESHOLD:
            return 1

        return max(1, len(change_counts))

    def detect_burnout_risk(self, timestamp_data: list[datetime | str]) -> str:
        """Detect sustained developer burnout risk from commit timestamp patterns.

        Analyses whether commits are occurring every day of the week for 3 or more
        consecutive weeks, indicating unsustainable working patterns.

        Args:
            timestamp_data: List of commit timestamps as datetime objects or ISO-8601
                            strings. Example: ["2026-03-01T22:00:00Z", ...]

        Returns:
            'High' if commits occur 7 days a week for 3+ consecutive weeks.
            'Moderate' if commits occur 6+ days a week for 2+ consecutive weeks.
            'Low' otherwise.
        """
        if not timestamp_data:
            return "Low"

        parsed: list[datetime] = []
        for ts in timestamp_data:
            if isinstance(ts, str):
                parsed.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            else:
                parsed.append(ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc))

        by_week: dict[tuple[int, int], set[int]] = {}
        for dt in parsed:
            iso = dt.isocalendar()
            week_key = (iso.year, iso.week)
            by_week.setdefault(week_key, set()).add(iso.weekday)

        sorted_weeks = sorted(by_week.keys())

        for days_threshold, weeks_threshold, label in [
            (self._BURNOUT_COMMIT_DAYS_PER_WEEK, self._BURNOUT_SUSTAINED_WEEKS, "High"),
            (6, 2, "Moderate"),
        ]:
            streak = 0
            for week in sorted_weeks:
                if len(by_week[week]) >= days_threshold:
                    streak += 1
                    if streak >= weeks_threshold:
                        return label
                else:
                    streak = 0

        return "Low"

    def get_hotspot_status(self, complexity_score: int, bug_frequency: int) -> str:
        """Classify a module's hotspot risk based on complexity and defect density.

        Args:
            complexity_score: AI-derived cyclomatic complexity score (integer).
            bug_frequency: Number of recorded defects or regressions in the module.

        Returns:
            'Critical Hotspot' when complexity > 15 and bug_frequency > 5 (Red tier).
            'Stable Logic' when complexity > 10 but bug criteria not met (Green tier).
            'Routine Module' otherwise (Neutral tier).
        """
        if complexity_score > self._CRITICAL_COMPLEXITY and bug_frequency > self._CRITICAL_BUG_FREQUENCY:
            return "Critical Hotspot"

        if complexity_score > self._ELEVATED_COMPLEXITY:
            return "Stable Logic"

        return "Routine Module"
