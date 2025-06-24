"""Generalized flashcard model using JSON content for flexible rendering."""

from beanie import Document
from pydantic import Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FlashcardType(str, Enum):
    """Enum for different flashcard types."""
    TWO_SIDED = "two_sided"
    FILL_IN_BLANK = "fill_in_blank"
    MULTIPLE_CHOICE = "multiple_choice"


class DifficultyLevel(str, Enum):
    """Enum for difficulty levels used in spaced repetition."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class Flashcard(Document):
    """Generalized flashcard model with JSON content for flexible rendering."""

    # Identification
    user_id: int = Field(..., description="Telegram user ID who owns this flashcard")

    # Type and content
    type: FlashcardType = Field(..., description="Type of flashcard for rendering")
    title: Optional[str] = Field(None, description="Optional title for the flashcard")
    content: Dict[str, Any] = Field(..., description="JSON content defining the flashcard structure")

    # Spaced repetition fields
    due_date: datetime = Field(
        default_factory=datetime.now, description="When this card is due for review"
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Current difficulty level"
    )
    repetition_count: int = Field(
        default=0, description="Number of times this card has been reviewed"
    )
    ease_factor: float = Field(
        default=2.5, description="Ease factor for spaced repetition algorithm"
    )
    interval_days: int = Field(default=1, description="Current interval in days")

    # Organization
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorizing the flashcard"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata for the flashcard"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, description="When the card was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="When the card was last updated"
    )

    # Statistics
    times_correct: int = Field(
        default=0, description="Number of times answered correctly"
    )
    times_incorrect: int = Field(
        default=0, description="Number of times answered incorrectly"
    )

    class Settings:
        name = "flashcards"

    @field_validator('content')
    @classmethod
    def validate_content_structure(cls, v, info):
        """Validate that content matches the expected structure for the flashcard type."""
        flashcard_type = info.data.get('type')
        
        if flashcard_type == FlashcardType.TWO_SIDED:
            required_fields = ['front', 'back']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Two-sided card missing required field: {field}")
                    
        elif flashcard_type == FlashcardType.FILL_IN_BLANK:
            required_fields = ['text_with_blanks', 'answers']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Fill-in-blank card missing required field: {field}")
            if not isinstance(v.get('answers'), list):
                raise ValueError("Fill-in-blank 'answers' must be a list")
                
        elif flashcard_type == FlashcardType.MULTIPLE_CHOICE:
            required_fields = ['question', 'options', 'correct_indices']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Multiple choice card missing required field: {field}")
            if not isinstance(v.get('options'), list):
                raise ValueError("Multiple choice 'options' must be a list")
            if not isinstance(v.get('correct_indices'), list):
                raise ValueError("Multiple choice 'correct_indices' must be a list")
                
        return v

    def get_question(self) -> str:
        """Get the question text for this card based on its type."""
        if self.type == FlashcardType.TWO_SIDED:
            return self.content.get('front', '')
            
        elif self.type == FlashcardType.FILL_IN_BLANK:
            text = self.content.get('text_with_blanks', '')
            # Replace blanks with underscores for display
            return text.replace('___', '_____')
            
        elif self.type == FlashcardType.MULTIPLE_CHOICE:
            question = self.content.get('question', '')
            options = self.content.get('options', [])
            
            # Format options with letters
            formatted_options = []
            for i, option in enumerate(options):
                formatted_options.append(f"{chr(65 + i)}. {option}")
            
            return f"{question}\n\n" + "\n".join(formatted_options)
            
        return ""

    def check_answer(self, user_input: Any) -> bool:
        """Check if the user's answer is correct based on flashcard type."""
        if self.type == FlashcardType.TWO_SIDED:
            correct_answer = self.content.get('back', '')
            return str(user_input).lower().strip() == correct_answer.lower().strip()
            
        elif self.type == FlashcardType.FILL_IN_BLANK:
            correct_answers = self.content.get('answers', [])
            case_sensitive = self.content.get('case_sensitive', False)
            
            if not isinstance(user_input, list):
                user_input = [str(user_input)]
                
            if len(user_input) != len(correct_answers):
                return False
                
            for user_ans, correct_ans in zip(user_input, correct_answers):
                if case_sensitive:
                    if str(user_ans).strip() != str(correct_ans).strip():
                        return False
                else:
                    if str(user_ans).lower().strip() != str(correct_ans).lower().strip():
                        return False
            return True
            
        elif self.type == FlashcardType.MULTIPLE_CHOICE:
            correct_indices = self.content.get('correct_indices', [])
            
            if not isinstance(user_input, list):
                user_input = [user_input]
                
            # Convert to integers if they're not already
            try:
                user_indices = [int(x) for x in user_input]
                return sorted(user_indices) == sorted(correct_indices)
            except (ValueError, TypeError):
                return False
                
        return False

    def get_answer_hint(self) -> str:
        """Get a hint about the expected answer format."""
        if self.type == FlashcardType.TWO_SIDED:
            return "Type your answer"
            
        elif self.type == FlashcardType.FILL_IN_BLANK:
            answers = self.content.get('answers', [])
            if len(answers) == 1:
                return "Fill in the blank"
            else:
                return f"Fill in the {len(answers)} blanks (separate with commas)"
                
        elif self.type == FlashcardType.MULTIPLE_CHOICE:
            correct_indices = self.content.get('correct_indices', [])
            allow_multiple = self.content.get('allow_multiple', False)
            
            if allow_multiple or len(correct_indices) > 1:
                return "Select one or more options (e.g., A, B, C)"
            else:
                return "Select one option (A, B, C, etc.)"
                
        return "Answer the question"


# Factory functions for creating specific flashcard types
def create_two_sided_card(
    user_id: int,
    front: str,
    back: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Flashcard:
    """Create a two-sided flashcard."""
    return Flashcard(
        user_id=user_id,
        type=FlashcardType.TWO_SIDED,
        title=title,
        content={
            "front": front,
            "back": back
        },
        tags=tags or [],
        metadata=metadata or {}
    )


def create_fill_in_blank_card(
    user_id: int,
    text_with_blanks: str,
    answers: List[str],
    case_sensitive: bool = False,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Flashcard:
    """Create a fill-in-the-blank flashcard."""
    return Flashcard(
        user_id=user_id,
        type=FlashcardType.FILL_IN_BLANK,
        title=title,
        content={
            "text_with_blanks": text_with_blanks,
            "answers": answers,
            "case_sensitive": case_sensitive
        },
        tags=tags or [],
        metadata=metadata or {}
    )


def create_multiple_choice_card(
    user_id: int,
    question: str,
    options: List[str],
    correct_indices: List[int],
    allow_multiple: bool = False,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Flashcard:
    """Create a multiple choice flashcard."""
    return Flashcard(
        user_id=user_id,
        type=FlashcardType.MULTIPLE_CHOICE,
        title=title,
        content={
            "question": question,
            "options": options,
            "correct_indices": correct_indices,
            "allow_multiple": allow_multiple
        },
        tags=tags or [],
        metadata=metadata or {}
    )