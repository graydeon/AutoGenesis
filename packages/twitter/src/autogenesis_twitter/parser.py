"""Tweet content parser — structured extraction with injection filtering.

Extracts tweets from raw page text into TweetData objects.
Uses configurable selectors for DOM-independent extraction.
Filters injection attempts before content reaches the LLM.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from autogenesis_twitter.models import TweetData, TweetMetrics

_SELECTORS_PATH = Path(__file__).parent / "selectors.json"
_MAX_TWEET_TEXT = 500


def _load_selectors() -> dict[str, Any]:
    """Load selector patterns from config file."""
    with _SELECTORS_PATH.open() as f:
        return json.load(f)


def _compile_injection_patterns(selectors: dict[str, Any]) -> list[re.Pattern[str]]:
    """Compile injection detection regex patterns."""
    return [re.compile(p, re.IGNORECASE) for p in selectors.get("injection_patterns", [])]


_SELECTORS = _load_selectors()
_INJECTION_PATTERNS = _compile_injection_patterns(_SELECTORS)


def is_injection_attempt(text: str) -> bool:
    """Check if text contains prompt injection patterns."""
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def extract_tweets_from_text(raw_text: str) -> list[TweetData]:
    """Extract structured tweets from raw page text.

    Parses the text looking for tweet patterns:
    @author · timestamp
    tweet text
    N replies · N retweets · N likes
    """
    tweets: list[TweetData] = []
    author_pattern = re.compile(r"(@[\w]+)\s*·\s*(\d+[hms]|\d{1,2}:\d{2})")
    metrics_pattern = re.compile(
        r"(\d+)\s+repl(?:y|ies).*?(\d+)\s+retweets?.*?(\d+)\s+likes?",
        re.IGNORECASE,
    )

    lines = raw_text.strip().split("\n")
    i = 0
    tweet_id = 0

    while i < len(lines):
        line = lines[i].strip()
        author_match = author_pattern.search(line)

        if author_match:
            author = author_match.group(1)
            timestamp = author_match.group(2)

            # Collect tweet text (next lines until metrics line)
            text_lines: list[str] = []
            i += 1
            while i < len(lines):
                current = lines[i].strip()
                if metrics_pattern.search(current) or author_pattern.search(current):
                    break
                if current:
                    text_lines.append(current)
                i += 1

            text = " ".join(text_lines)
            if len(text) > _MAX_TWEET_TEXT:
                text = text[:_MAX_TWEET_TEXT]

            # Parse metrics if present
            metrics = TweetMetrics()
            if i < len(lines):
                m = metrics_pattern.search(lines[i].strip())
                if m:
                    metrics = TweetMetrics(
                        replies=int(m.group(1)),
                        retweets=int(m.group(2)),
                        likes=int(m.group(3)),
                    )
                    i += 1

            tweet_id += 1
            tweets.append(
                TweetData(
                    id=str(tweet_id),
                    author=author,
                    text=text,
                    metrics=metrics,
                    timestamp=timestamp,
                )
            )
        else:
            i += 1

    return tweets


def format_tweet_for_llm(tweet: TweetData) -> str:
    """Wrap tweet in tagged boundaries for safe LLM consumption."""
    return (
        f'[UNTRUSTED_TWEET_CONTENT author="{tweet.author}" id="{tweet.id}"]\n'
        f"{tweet.text}\n"
        f"[/UNTRUSTED_TWEET_CONTENT]"
    )
