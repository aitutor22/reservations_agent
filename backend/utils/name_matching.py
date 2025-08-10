"""
Name Matching Utilities
Provides fuzzy name matching for reservation verification
"""

def calculate_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to change one word into another.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        The Levenshtein distance between s1 and s2
    """
    if len(s1) < len(s2):
        return calculate_levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    # Create a row for the previous distances
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        # Create a new row for current distances
        current_row = [i + 1]
        
        for j, c2 in enumerate(s2):
            # Calculate cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            current_row.append(min(insertions, deletions, substitutions))
        
        previous_row = current_row
    
    return previous_row[-1]


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison.
    
    Args:
        name: The name to normalize
        
    Returns:
        Normalized name (lowercase, stripped, single spaces)
    """
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Replace multiple spaces with single space
    import re
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def names_match(provided_name: str, stored_name: str, max_distance: int = 2) -> bool:
    """
    Check if two names match using fuzzy matching.
    
    This function normalizes both names and then checks if they are similar enough
    based on Levenshtein distance. This helps handle transcription errors from
    voice input.
    
    Args:
        provided_name: The name provided by the user
        stored_name: The name stored in the database
        max_distance: Maximum allowed Levenshtein distance (default: 2)
        
    Returns:
        True if names match (exact or within distance threshold), False otherwise
    """
    # Normalize both names
    normalized_provided = normalize_name(provided_name)
    normalized_stored = normalize_name(stored_name)
    
    # Check for exact match first (most common case)
    if normalized_provided == normalized_stored:
        return True
    
    # Check if one name contains the other (e.g., "Dan" vs "Dan Smith")
    if normalized_provided in normalized_stored or normalized_stored in normalized_provided:
        # But only if the shorter name is at least 3 characters
        shorter_name = min(normalized_provided, normalized_stored, key=len)
        if len(shorter_name) >= 3:
            return True
    
    # Calculate Levenshtein distance for fuzzy matching
    distance = calculate_levenshtein_distance(normalized_provided, normalized_stored)
    
    # Allow fuzzy match based on distance threshold
    return distance <= max_distance


def split_and_match_names(provided_name: str, stored_name: str, max_distance: int = 2) -> bool:
    """
    Enhanced name matching that handles first/last name variations.
    
    This function can match:
    - "John Smith" with "John" or "Smith"
    - "John" with "John Smith"
    - Fuzzy matches on any part
    
    Args:
        provided_name: The name provided by the user
        stored_name: The name stored in the database
        max_distance: Maximum allowed Levenshtein distance
        
    Returns:
        True if names match in any reasonable way
    """
    # First try the basic match
    if names_match(provided_name, stored_name, max_distance):
        return True
    
    # Split names into parts
    provided_parts = normalize_name(provided_name).split()
    stored_parts = normalize_name(stored_name).split()
    
    # If either is a single name, check if it matches any part of the other
    if len(provided_parts) == 1:
        for stored_part in stored_parts:
            if names_match(provided_name, stored_part, max_distance):
                return True
    
    if len(stored_parts) == 1:
        for provided_part in provided_parts:
            if names_match(provided_part, stored_name, max_distance):
                return True
    
    # Check if first names match (common for reservations)
    if provided_parts and stored_parts:
        if names_match(provided_parts[0], stored_parts[0], max_distance):
            return True
    
    return False