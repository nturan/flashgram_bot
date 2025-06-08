"""Suffix extraction utilities for Russian morphology."""

import logging

logger = logging.getLogger(__name__)


class SuffixExtractor:
    """Extracts suffixes from inflected Russian words."""
    
    def extract_suffix(self, dictionary_form: str, inflected_form: str) -> tuple[str, str]:
        """Extract the suffix from an inflected form.
        Returns (stem, suffix) where stem + suffix = inflected_form"""
        try:
            # Find the common prefix (stem)
            dict_lower = dictionary_form.lower()
            inflected_lower = inflected_form.lower()
            
            # Find longest common prefix
            common_length = 0
            min_length = min(len(dict_lower), len(inflected_lower))
            
            for i in range(min_length):
                if dict_lower[i] == inflected_lower[i]:
                    common_length += 1
                else:
                    break
            
            # If no common prefix or very short, use a safe minimum
            if common_length < 2:
                # For very different forms, take at least 2 characters as stem
                safe_stem_length = min(2, len(inflected_form) - 1)
                stem = inflected_form[:safe_stem_length]
                suffix = inflected_form[safe_stem_length:]
            else:
                # Use the common prefix as stem, but ensure we don't go too far
                # Leave at least 1 character for the suffix if possible
                if common_length >= len(inflected_form):
                    stem = inflected_form[:-1] if len(inflected_form) > 1 else inflected_form
                    suffix = inflected_form[-1:] if len(inflected_form) > 1 else ""
                else:
                    stem = inflected_form[:common_length]
                    suffix = inflected_form[common_length:]
            
            return stem, suffix
            
        except Exception as e:
            logger.error(f"Error extracting suffix from '{dictionary_form}' -> '{inflected_form}': {e}")
            # Fallback: take first half as stem, second half as suffix
            mid_point = len(inflected_form) // 2
            return inflected_form[:mid_point], inflected_form[mid_point:]