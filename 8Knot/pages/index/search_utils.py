"""
Search utilities for the 8Knot application.
Provides improved search algorithms for the searchbar.
"""
from typing import List, Dict, Any
import re
from difflib import SequenceMatcher

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    The Levenshtein distance is the minimum number of single-character edits 
    (insertions, deletions, or substitutions) required to change one string into another.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        int: The Levenshtein distance between s1 and s2
    """
    # Convert both strings to lowercase for case-insensitive matching
    s1, s2 = s1.lower(), s2.lower()
    
    # Create a matrix of size (len(s1)+1) x (len(s2)+1)
    # Where matrix[i][j] will hold the Levenshtein distance between
    # the first i characters of s1 and the first j characters of s2
    rows, cols = len(s1) + 1, len(s2) + 1
    dist = [[0 for _ in range(cols)] for _ in range(rows)]
    
    # Initialize the first row and column with the distance from empty string
    for i in range(rows):
        dist[i][0] = i
    for j in range(cols):
        dist[0][j] = j
    
    # Fill in the rest of the matrix
    for i in range(1, rows):
        for j in range(1, cols):
            # If characters match, cost is 0, otherwise 1
            cost = 0 if s1[i-1] == s2[j-1] else 1
            
            # Calculate minimum of three possible operations
            dist[i][j] = min(
                dist[i-1][j] + 1,      # deletion
                dist[i][j-1] + 1,      # insertion
                dist[i-1][j-1] + cost  # substitution
            )
    
    # Return the distance
    return dist[rows-1][cols-1]

def levenshtein_score(s1: str, s2: str) -> float:
    """
    Calculate a similarity score based on Levenshtein distance.
    
    Args:
        s1: First string (typically the search query)
        s2: Second string (typically the option label)
        
    Returns:
        float: Score between 0 and 1, where 1 is a perfect match
    """
    # Calculate the Levenshtein distance
    distance = levenshtein_distance(s1, s2)
    
    # Get the maximum possible distance (which is the length of the longer string)
    max_distance = max(len(s1), len(s2))
    
    # If both strings are empty, they are identical
    if max_distance == 0:
        return 1.0
    
    # Calculate the similarity score (1 - normalized distance)
    # The closer to 0 the distance is, the closer to 1 the score will be
    return 1.0 - (distance / max_distance)

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
    Calculate match score based on tokens using Levenshtein distance.
    
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
    
    # Check for token matches with Levenshtein distance
    match_scores = []
    for token in tokens:
        # Try exact contains first
        if token in label_lower:
            match_scores.append(0.95)
            continue
            
        # If no exact match, calculate best score against label tokens
        best_score = 0.0
        for label_token in label_tokens:
            # Use Levenshtein for better matching with typos
            score = levenshtein_score(token, label_token)
            best_score = max(best_score, score)
        
        match_scores.append(best_score)
    
    # Average the scores
    if match_scores:
        return sum(match_scores) / len(match_scores)
    return 0.0

def fuzzy_search(query: str, options: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
    """
    Perform fuzzy search on a list of options using Levenshtein distance.
    
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
    
    # Score options based on multiple criteria
    scored_options = []
    for option in options:
        label = option["label"]
        
        # Calculate full query score using Levenshtein distance
        full_score = levenshtein_score(query, label)
        
        # Calculate token-based score
        token_score = token_match_score(tokens, label)
        
        # Bonus for substring match
        substring_score = 0.0
        if query in label.lower():
            substring_score = 0.95
            if label.lower().startswith(query):
                substring_score = 1.0
        
        # Use the best score from all methods
        final_score = max(full_score, token_score, substring_score)
        
        if final_score >= threshold:
            scored_options.append((final_score, option))
    
    # Sort by score descending and return only the options
    return [opt for score, opt in sorted(scored_options, key=lambda x: x[0], reverse=True)] 