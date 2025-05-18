"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any
import re

# Going with rapidfuzz instead of fuzzywuzzy
# as it's more performant and supports score_cutoff
from rapidfuzz import fuzz, process


def search_short_query(query: str, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Optimized search for very short queries (1-2 characters).
    Uses simple prefix and contains matching for better performance.

    Args:
        query: Short search query string
        options: List of dictionaries with 'label' and 'value' keys

    Returns:
        List of matching options prioritizing prefix matches
    """
    starts_with_matches = []
    contains_matches = []
    query_lower = query.lower()

    # Separate into prefix matches and contains matches
    for option in options:
        # Get the label and convert to lowercase once
        label = option["label"].lower()
        if label.startswith(query_lower):
            starts_with_matches.append(option)
        elif query_lower in label:
            contains_matches.append(option)

    # Limit results
    max_starts_with = min(50, len(starts_with_matches))
    max_contains = min(50, len(contains_matches))

    return starts_with_matches[:max_starts_with] + contains_matches[:max_contains]


def search_with_fuzzy_matching(query: str, options: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search using the rapidfuzz library for longer queries.

    Args:
        query: Search query string
        options: List of dictionaries with 'label' and 'value' keys
        threshold: Minimum similarity score to include in results (0-1)

    Returns:
        List of matching options sorted by relevance
    """
    # Convert threshold to the 0-100 scale used by rapidfuzz
    threshold_100 = int(threshold * 100)

    # Extract matches with scores above threshold
    matches = process.extract(
        query,
        [opt["label"] for opt in options],
        scorer=fuzz.token_sort_ratio,
        processor=str.lower,  # Case-insensitive matching
        limit=100,
        score_cutoff=threshold_100,
    )

    # Map back to original option objects
    options_dict = {opt["label"]: opt for opt in options}
    result = []

    # Handle the return format from rapidfuzz which returns (match, score, index)
    for match_data in matches:
        # Extract just the label (first element)
        label = match_data[0]
        if label in options_dict:
            result.append(options_dict[label])

    return result


def calculate_token_score(token: str, label: str, label_tokens: List[str]) -> float:
    """
    Calculate the match score for a single token against a label.

    Args:
        token: Single search token
        label: Full label
        label_tokens: Tokenized version of the label

    Returns:
        float: Score between 0 and 1 representing match quality
    """
    # Try exact contains first (high confidence match)
    if token in label:
        return 0.95

    # If no exact match, find best fuzzy match among label tokens
    best_score = 0.0
    for label_token in label_tokens:
        # Use rapidfuzz's token_sort_ratio for better matching
        score = fuzz.token_sort_ratio(token, label_token) / 100.0
        best_score = max(best_score, score)

    return best_score


def fuzzy_search(query: str, options: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of options using rapidfuzz, case-insensitive.

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
        return search_short_query(query, options)
    else:
        return search_with_fuzzy_matching(query, options, threshold)


def tokenize_search(query: str) -> List[str]:  # Function breaks down a search query into smaller parts (tokens)
    """
    Split search query into tokens for more flexible matching.

    token -> meaningful unit of text extracted from a larger string
    example: if the search query is "Project Aspen: 8Knot and Augur", then the tokens are ["project", "aspen", "8knot", "augur"]

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

    # Convert to lowercase once
    label_lower = label.lower()
    # tokenize_search already handles lowercase conversion internally
    label_tokens = tokenize_search(label)

    # Calculate individual token match scores
    match_scores = [calculate_token_score(token, label_lower, label_tokens) for token in tokens]

    # Average the scores
    if match_scores:
        return sum(match_scores) / len(match_scores)
    return 0.0
