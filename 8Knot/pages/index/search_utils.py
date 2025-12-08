"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any, Optional
import re
import bisect

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


def search_with_fuzzy_matching(
    query: str, options: List[Dict[str, Any]], threshold: float, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search using the rapidfuzz library for longer queries.
    Enhanced to prioritize exact substring matches.

    Args:
        query: Search query string
        options: List of dictionaries with 'label' and 'value' keys
        threshold: Minimum similarity score to include in results (0-1)
        limit: Maximum number of results to return (None = all results)

    Returns:
        List of matching options sorted by relevance
    """
    if not options:
        return []

    # Convert threshold to the 0-100 scale used by rapidfuzz
    threshold_100 = int(threshold * 100)
    query_lower = query.lower()

    exact_matches = []
    fuzzy_matches = []

    # First pass: find exact substring matches (highest priority)
    for opt in options:
        label_lower = opt["label"].lower()
        if query_lower in label_lower:
            exact_matches.append(opt)
            # Early termination if we have enough exact matches and limit is set
            if limit and len(exact_matches) >= limit:
                return exact_matches[:limit]

    # Second pass: find fuzzy matches for items not already matched exactly
    exact_labels = set(opt["label"] for opt in exact_matches)
    remaining_options = [opt for opt in options if opt["label"] not in exact_labels]

    if remaining_options:
        # Calculate how many fuzzy matches we need (if limit is set)
        fuzzy_limit = None
        if limit:
            fuzzy_limit = max(0, limit - len(exact_matches))
            if fuzzy_limit == 0:
                return exact_matches  # Already have enough exact matches

        # Use fuzzy matching for remaining options
        matches = process.extract(
            query_lower,  # Use lowercased query
            [opt["label"] for opt in remaining_options],
            scorer=fuzz.token_sort_ratio,
            processor=str.lower,
            limit=fuzzy_limit,  # Use calculated limit or None for comprehensive
            score_cutoff=threshold_100,
        )

        # Map back to original option objects
        remaining_options_dict = {opt["label"]: opt for opt in remaining_options}

        # Handle the return format from rapidfuzz which returns (match, score, index)
        for match_data in matches:
            # Extract just the label (first element)
            label = match_data[0]
            if label in remaining_options_dict:
                fuzzy_matches.append(remaining_options_dict[label])

    # Combine results: exact matches first, then fuzzy matches
    return exact_matches + fuzzy_matches


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


def fuzzy_search(
    query: str, options: List[Dict[str, Any]], threshold: float = 0.2, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of options using rapidfuzz, case-insensitive.

    Args:
        query: Search query string
        options: List of dictionaries with 'label' and 'value' keys
        threshold: Minimum similarity score to include in results (0-1)
        limit: Maximum number of results to return (None = all results)

    Returns:
        List of matching options sorted by relevance
    """
    if not query:
        return options

    # For very short queries (1-2 chars), use a simpler and faster matching approach
    if len(query) <= 2:
        return search_short_query(query, options)
    else:
        return search_with_fuzzy_matching(query, options, threshold, limit)


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


def get_adaptive_debounce_time(query: str) -> int:
    """
    Calculate adaptive debounce time based on query length.

    Strategy inspired by Spotify and YouTube:
    - Short queries (1-3 chars): Longer debounce (800-400ms) - user likely still typing
    - Medium queries (4-5 chars): Medium debounce (250ms) - user may be finishing
    - Long queries (6+ chars): Shorter debounce (150ms) - user likely finished

    Args:
        query: The search query string

    Returns:
        Debounce time in milliseconds
    """
    if not query:
        return 200  # Default for empty query

    query_length = len(query.strip())
    if query_length == 0:
        return 200  # Treat whitespace-only as empty query

    # Debounce thresholds: sorted max_lengths for bisect lookup
    # O(log n) lookup using binary search (though n=4, so effectively O(1))
    _THRESHOLD_LENGTHS = [1, 2, 3, 5]  # Sorted for bisect
    _DEBOUNCE_VALUES = [800, 600, 400, 250]  # Corresponding debounce times
    _DEFAULT_DEBOUNCE = 150  # For queries longer than 5 chars

    # Use bisect_left to find the smallest threshold >= query_length
    # This finds the leftmost position where query_length could be inserted
    # Example: query_length=4 → bisect_left returns 3 (first threshold >= 4, which is 5)
    index = bisect.bisect_left(_THRESHOLD_LENGTHS, query_length)

    # If index is within bounds, use the corresponding debounce value
    if index < len(_DEBOUNCE_VALUES):
        return _DEBOUNCE_VALUES[index]

    # For queries longer than the max threshold (5), return default
    return _DEFAULT_DEBOUNCE


def clean_repo_name(repo_name: str) -> tuple[str, str]:
    """
    Clean repository names by removing GitHub and GitLab URL prefixes.

    Supports both GitHub and GitLab repositories for future compatibility.

    Args:
        repo_name: The original repository name/URL

    Returns:
        Tuple of (cleaned_name, platform) where platform is 'github', 'gitlab', or 'unknown'
    """
    if not repo_name:
        return repo_name, "unknown"

    # Define prefixes with their corresponding platforms
    github_prefixes = ["https://github.com/"]

    gitlab_prefixes = ["https://gitlab.com/"]

    cleaned_name = repo_name
    repo_name_lower = repo_name.lower()

    # Check GitHub prefixes
    for prefix in github_prefixes:
        if repo_name_lower.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix) :]
            return cleaned_name, "github"

    # Check GitLab prefixes
    for prefix in gitlab_prefixes:
        if repo_name_lower.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix) :]
            return cleaned_name, "gitlab"

    # No known prefix found
    return cleaned_name, "unknown"
