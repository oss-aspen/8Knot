"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any
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
    Calculate match score based on tokens.
    
    Args:
        tokens: List of search tokens
        label: String to match against
        
    Returns:
        float: Score between 0 and 1
    """
    if not tokens:
        return 0.0
        
    label_lower = label.lower()
    
    # Check for exact token matches
    match_scores = []
    for token in tokens:
        if token in label_lower:
            # Higher score for token matches
            match_scores.append(0.9)
        else:
            # For non-exact matches, calculate fuzzy score
            best_score = 0
            label_tokens = tokenize_search(label_lower)
            for label_token in label_tokens:
                score = simple_fuzzy_score(token, label_token)
                best_score = max(best_score, score)
            match_scores.append(best_score)
    
    # Average the scores
    if match_scores:
        return sum(match_scores) / len(match_scores)
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
    
    query = query.lower()
    tokens = tokenize_search(query)
    
    # Score options based on both full query and tokens
    scored_options = []
    for option in options:
        label = option["label"]
        
        # Calculate full query score
        full_score = simple_fuzzy_score(query, label)
        
        # Calculate token-based score
        token_score = token_match_score(tokens, label)
        
        # Use the better of the two scores
        final_score = max(full_score, token_score)
        
        if final_score >= threshold:
            scored_options.append((final_score, option))
    
    # Sort by score descending and return only the options
    return [opt for score, opt in sorted(scored_options, key=lambda x: x[0], reverse=True)] 