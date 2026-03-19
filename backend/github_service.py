import logging
import re
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException


logger = logging.getLogger(__name__)


class GitHubService:
    """Service class for fetching and parsing commit diffs from GitHub."""

    GITHUB_API_BASE = "https://api.github.com"

    async def fetch_commit_diff(self, repo_url: str, commit_sha: str) -> str:
        """Fetch a commit diff from the GitHub API.

        Args:
            repo_url: Full repository URL, such as 'https://github.com/owner/repo'.
            commit_sha: Target commit SHA.

        Returns:
            Raw diff text for the commit.

        Raises:
            HTTPException: If the repository URL is invalid or GitHub returns known errors.
        """
        owner, repo = self._parse_owner_repo(repo_url)
        endpoint = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{commit_sha}"

        headers = {"Accept": "application/vnd.github.v3.diff"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, headers=headers)

        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        if rate_limit_remaining and rate_limit_remaining.isdigit() and int(rate_limit_remaining) < 10:
            logger.warning(
                "GitHub API rate limit low: remaining=%s endpoint=%s",
                rate_limit_remaining,
                endpoint,
            )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="GitHub commit or repository not found.",
            )

        if response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="GitHub API access forbidden or rate limit exceeded.",
            )

        if response.is_error:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub API request failed with status {response.status_code}.",
            )

        return response.text

    def parse_diff_metadata(self, diff_text: str) -> dict:
        """Extract changed file metadata from a unified diff payload.

        Args:
            diff_text: Raw unified diff text.

        Returns:
            Dictionary containing unique changed filenames and file count.
        """
        matches = re.findall(r"^diff --git a/(.+?) b/(.+?)$", diff_text, flags=re.MULTILINE)

        changed_files = []
        seen = set()
        for left_name, right_name in matches:
            candidate = right_name or left_name
            if candidate not in seen:
                seen.add(candidate)
                changed_files.append(candidate)

        return {
            "changed_files": changed_files,
            "file_count": len(changed_files),
        }

    def _parse_owner_repo(self, repo_url: str) -> tuple[str, str]:
        """Parse a GitHub repository URL into owner and repository name.

        Args:
            repo_url: GitHub repository URL.

        Returns:
            A tuple of (owner, repo).

        Raises:
            HTTPException: If the URL is not a valid GitHub repository URL.
        """
        parsed = urlparse(repo_url.strip())
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")

        path_parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(path_parts) < 2:
            raise HTTPException(status_code=400, detail="Repository URL must include owner and repo name.")

        owner = path_parts[0]
        repo = path_parts[1].removesuffix(".git")

        if not owner or not repo:
            raise HTTPException(status_code=400, detail="Invalid owner or repository name in URL.")

        return owner, repo
