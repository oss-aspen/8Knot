"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from rapidfuzz import process


def fuzzy_search(query: str, options: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of options using fuzzywuzzy, case-insensitive.
    Args:
        query: Search query string
        options: List of dictionaries with 'label' and 'value' keys
        threshold: Minimum similarity score to include in results (0-1)
    Returns:
        List of matching options sorted by relevance
    """
    if not query:
        return options

    # For very short queries (1-2 chars), use a simpler and faster matching approach
    if len(query) <= 2:
        starts_with_matches = []
        contains_matches = []
        query_lower = query.lower()
        for option in options:
            label_lower = option["label"].lower()
            if label_lower.startswith(query_lower):
                starts_with_matches.append(option)
            elif query_lower in label_lower:
                contains_matches.append(option)
        max_starts_with = min(50, len(starts_with_matches))
        max_contains = min(50, len(contains_matches))
        return starts_with_matches[:max_starts_with] + contains_matches[:max_contains]

    threshold_100 = int(threshold * 100)
    matches = process.extract(
        query,
        [opt["label"] for opt in options],
        scorer=fuzz.token_sort_ratio,
        processor=str.lower,  # Case-insensitive matching
        limit=100,
        score_cutoff=threshold_100,
    )
    options_dict = {opt["label"]: opt for opt in options}
    return [options_dict[label] for label, score in matches]


def tokenize_search(query: str) -> List[str]:
    """
    Split search query into tokens for more flexible matching.

    Args:
        query: Search query string

    Returns:
        List of tokens from the query
    """
    return [token.strip().lower() for token in re.split(r"[\s/_.,-]+", query) if token.strip()]


def token_match_score(tokens: List[str], label: str) -> float:
    """
    Calculate match score based on tokens using fuzzywuzzy.

    Args:
        tokens: List of search tokens
        label: String to match against

    Returns:
        float: Score between 0 and 1
    """
    if not tokens:
        return 0.0

    label_lower = label.lower()
    label_tokens = tokenize_search(label_lower)

    # Check for token matches with fuzzywuzzy
    match_scores = []
    for token in tokens:
        # Try exact contains first
        if token in label_lower:
            match_scores.append(0.95)
            continue

        # If no exact match, calculate best score against label tokens
        best_score = 0.0
        for label_token in label_tokens:
            # Use fuzzywuzzy's token_sort_ratio for better matching
            score = fuzz.token_sort_ratio(token, label_token) / 100.0
            best_score = max(best_score, score)

        match_scores.append(best_score)

    # Average the scores
    if match_scores:
        return sum(match_scores) / len(match_scores)
    return 0.0
