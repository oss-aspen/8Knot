"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any, Tuple
import re
from difflib import SequenceMatcher

def simple_fuzzy_score(s1: str, s2: str) -> float:
    """
    Calculate a simple fuzzy match score between two strings.
    
    Args:
        s1: First string (typically the search query)
        s2: Second string (typically the option label)
        
    Returns:
        float: Score between 0 and 1, where 1 is a perfect match
    """
    # Convert both strings to lowercase for case-insensitive matching
    s1, s2 = s1.lower(), s2.lower()
    
    # Check for exact substring match first (give it a high score)
    if s1 in s2:
        # If it's at the beginning of the string, give it an even higher score
        if s2.startswith(s1):
            return 1.0
        return 0.9
    
    # Use sequence matcher for fuzzy matching
    return SequenceMatcher(None, s1, s2).ratio()

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein (edit) distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        int: The number of edits needed to transform s1 into s2
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    # If s2 is empty, the distance is the length of s1
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Calculate insertions, deletions and substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def edit_distance_score(s1: str, s2: str) -> float:
    """
    Calculate a score based on edit distance, normalized to 0-1 range.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        float: Score between 0 and 1, where 1 means identical
    """
    if not s1 or not s2:
        return 0.0
    
    # Get edit distance
    distance = levenshtein_distance(s1, s2)
    
    # Normalize to 0-1 range (1 is perfect match)
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0  # Both strings empty
        
    return 1.0 - (distance / max_len)

def tokenize_search(query: str) -> List[str]:
    """
    Split search query into tokens for more flexible matching.
    
    Args:
        query: Search query string
        
    Returns:
        List of tokens from the query
    """
    return [token.strip().lower() for token in re.split(r'[\s/_.,-]+', query) if token.strip()]

def token_match_score(tokens: List[str], label: str) -> float:
    """
    Calculate match score based on tokens with improved typo handling.
    
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
    
    # Check for token matches with edit distance consideration
    match_scores = []
    for token in tokens:
        if token in label_lower:
            # Higher score for exact token matches
            match_scores.append(0.95)
            continue
            
        # For non-exact matches, try multiple approaches
        best_score = 0.0
        
        # 1. Check if token is similar to any part of the label using edit distance
        for i in range(len(label_lower) - len(token) + 1):
            substr = label_lower[i:i+len(token)]
            edit_score = edit_distance_score(token, substr)
            if edit_score > 0.7:  # High threshold for substring edit distance
                best_score = max(best_score, edit_score)
        
        # 2. Check against individual tokens in the label
        for label_token in label_tokens:
            # Use the better of sequence matching and edit distance
            seq_score = simple_fuzzy_score(token, label_token)
            edit_score = edit_distance_score(token, label_token)
            token_score = max(seq_score, edit_score)
            best_score = max(best_score, token_score)
        
        match_scores.append(best_score)
    
    # Weight more heavily if all tokens have good matches
    if all(score > 0.6 for score in match_scores):
        boost = 0.1  # Boost the score if all tokens match well
    else:
        boost = 0
        
    # Average the scores with potential boost
    if match_scores:
        avg_score = sum(match_scores) / len(match_scores)
        return min(1.0, avg_score + boost)  # Cap at 1.0
    return 0.0

def check_common_typos(query: str, label: str) -> float:
    """
    Check for common typo patterns and give higher scores for likely typos.
    Especially useful for repository names like "chaoss" -> "choss".
    
    Args:
        query: Search query
        label: Label to check against
        
    Returns:
        float: Score boost (0 if no special case found)
    """
    query_lower = query.lower()
    label_lower = label.lower()
    
    # No boost if exact match already exists
    if query_lower in label_lower:
        return 0.0
    
    # Special dictionary for common project names that are often misspelled
    common_projects = {
        # Variations of "chaoss" 
        "choss": "chaoss",
        "caoss": "chaoss",
        "chaos": "chaoss",
        "choass": "chaoss",
        "chaas": "chaoss",
        
        # Variations of "apache"
        "apche": "apache",
        "apach": "apache",
        "apace": "apache",
        "apahe": "apache",
    }
    
    # Extract the repository name from the label (after any prefix)
    repo_name = label_lower
    if ":" in label_lower:
        _, repo_name = label_lower.split(":", 1)
        repo_name = repo_name.strip()
    
    # Check if we're dealing with a common misspelling
    for misspelling, correct in common_projects.items():
        if misspelling in query_lower and correct in repo_name:
            return 0.6  # Very high boost for known misspellings
            
        # Also check the reverse - if the query has the correct spelling
        # but we're matching against a variation
        if correct in query_lower and misspelling in repo_name:
            return 0.6
    
    # Check direct edit distance
    if len(query_lower) > 2 and len(repo_name) > 2:
        edit_dist = levenshtein_distance(query_lower, repo_name)
        if edit_dist == 1:  # Just one character different
            return 0.5
        if edit_dist == 2 and len(query_lower) >= 5:  # Two characters but longer word
            return 0.3
    
    return 0.0  

def fuzzy_search(query: str, options: List[Dict[str, Any]], threshold: float = 0.3) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of options.
    
    Args:
        query: Search query string
        options: List of dictionaries with 'label' and 'value' keys
        threshold: Minimum similarity score to include in results
        
    Returns:
        List of matching options sorted by relevance
    """
    if not query:
        return options
    
    query = query.lower().strip()
    tokens = tokenize_search(query)
    
    # Score options based on multiple search techniques
    scored_options = []
    for option in options:
        label = option["label"]
        
        # Calculate full query score
        full_score = simple_fuzzy_score(query, label)
        
        # Calculate token-based score
        token_score = token_match_score(tokens, label)
        
        # Extract repository name (without prefix)
        repo_name = label.lower()
        if ":" in repo_name:
            _, repo_name = repo_name.split(":", 1)
            repo_name = repo_name.strip()
            
        # Check for common typos
        typo_boost = check_common_typos(query, label)
        
        # Combine scores, prioritizing the best match method
        final_score = max(full_score, token_score) + typo_boost
        final_score = min(1.0, final_score)  # Cap at 1.0
        
        if final_score >= threshold:
            scored_options.append((final_score, option))
    
    # Sort by score descending and return only the options
    return [opt for score, opt in sorted(scored_options, key=lambda x: x[0], reverse=True)]