"""Russian text extraction utilities."""

import re
from typing import List


def extract_russian_words(text: str) -> List[str]:
    """Extract Russian words from text, filtering out punctuation and non-Russian words.
    
    Args:
        text: Input text containing mixed content
        
    Returns:
        List of unique meaningful Russian words (>=3 characters)
    """
    # Remove punctuation and split into words
    # Cyrillic pattern to match Russian words
    russian_word_pattern = r'[а-яё]+(?:-[а-яё]+)*'
    words = re.findall(russian_word_pattern, text.lower())
    
    # Filter out very short words (likely particles/prepositions)
    meaningful_words = [word for word in words if len(word) >= 3]
    
    # Remove duplicates while preserving order
    unique_words = []
    seen = set()
    for word in meaningful_words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)
    
    return unique_words