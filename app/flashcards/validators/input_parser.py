"""Input parsing utilities for user answers."""

from typing import List


class InputParser:
    """Parses user input for different answer formats."""
    
    def parse_fill_in_blank_answer(self, user_input: str, expected_count: int) -> List[str]:
        """Parse user input for fill-in-the-blank questions."""
        # Split by common delimiters
        separators = [',', ';', '|', '\n']
        answers = [user_input.strip()]
        
        for sep in separators:
            if sep in user_input:
                answers = [ans.strip() for ans in user_input.split(sep)]
                break
        
        # Ensure we have the right number of answers
        while len(answers) < expected_count:
            answers.append("")
        
        return answers[:expected_count]
    
    def parse_multiple_choice_answer(self, user_input: str, option_count: int) -> List[int]:
        """Parse user input for multiple choice questions."""
        user_input = user_input.upper().strip()
        selected_indices = []
        
        # Handle letter inputs (A, B, C, etc.)
        for char in user_input:
            if char.isalpha():
                index = ord(char) - ord('A')
                if 0 <= index < option_count and index not in selected_indices:
                    selected_indices.append(index)
        
        # Handle number inputs (1, 2, 3, etc.)
        if not selected_indices:
            for char in user_input:
                if char.isdigit():
                    index = int(char) - 1  # Convert to 0-based
                    if 0 <= index < option_count and index not in selected_indices:
                        selected_indices.append(index)
        
        return sorted(selected_indices)