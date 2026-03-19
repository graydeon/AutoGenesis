"""Content guardrails — pre-engagement filter and constitutional self-check.

Two distinct classes:
- PreEngagementFilter: screens incoming tweets before the agent reasons about them
- ConstitutionalCheck: validates the agent's own output before queuing
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autogenesis_twitter.parser import is_injection_attempt

if TYPE_CHECKING:
    from autogenesis_twitter.models import TweetData

# Keywords suggesting AI/tech relevance
_TECH_KEYWORDS = re.compile(
    r"\b(ai|artificial intelligence|machine learning|ml|llm|gpt|claude|"
    r"neural|deep learning|transformer|model|open.?source|github|python|"
    r"javascript|typescript|rust|coding|programming|software|tech|api|"
    r"startup|developer|engineer|data science|compute|gpu|chip|token|"
    r"prompt|agent|autonomous|robot|automation)\b",
    re.IGNORECASE,
)

# Patterns indicating hate speech / bigotry (simplified — real system would use a classifier)
_HATE_PATTERNS = re.compile(
    r"\b(go back to|illegals?|subhuman|degenerate|groomer)\b",
    re.IGNORECASE,
)

# Patterns indicating identity leak
_IDENTITY_LEAK_PATTERNS = [
    re.compile(
        r"\bas an? (ai|artificial intelligence|language model|llm|chatbot|bot)\b", re.IGNORECASE
    ),
    re.compile(r"\bmy (training|training data|parameters|weights|model)\b", re.IGNORECASE),
    re.compile(
        r"\bi (was|am) (trained|programmed|designed|built|created) (to|by)\b", re.IGNORECASE
    ),
    re.compile(r"\bi don'?t have (feelings|emotions|consciousness|a body)\b", re.IGNORECASE),
]


class PreEngagementFilter:
    """Screens incoming tweets before the agent reasons about them."""

    def should_engage(self, tweet: TweetData) -> bool:
        """Return True if the tweet is safe and relevant to engage with."""
        if is_injection_attempt(tweet.text):
            return False
        if _HATE_PATTERNS.search(tweet.text):
            return False
        return bool(_TECH_KEYWORDS.search(tweet.text))


@dataclass
class CheckResult:
    """Result of a constitutional self-check."""

    passed: bool
    reason: str = ""


class ConstitutionalCheck:
    """Validates the agent's own output before queuing."""

    def check(self, draft_text: str) -> CheckResult:
        """Run all constitutional checks on a draft."""
        for pattern in _IDENTITY_LEAK_PATTERNS:
            if pattern.search(draft_text):
                return CheckResult(
                    passed=False, reason=f"Identity leak detected: {pattern.pattern}"
                )
        return CheckResult(passed=True)
