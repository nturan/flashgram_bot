from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union, Dict, Any
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

class BaseFlashcard(BaseModel):
    """Base flashcard model with common fields for all flashcard types."""
    
    # Identification
    id: Optional[str] = Field(None, description="Unique identifier (MongoDB ObjectId)")
    
    # Type and content
    type: FlashcardType = Field(..., description="Type of flashcard")
    title: Optional[str] = Field(None, description="Optional title for the flashcard")
    
    # Spaced repetition fields
    due_date: datetime = Field(default_factory=datetime.now, description="When this card is due for review")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Current difficulty level")
    repetition_count: int = Field(default=0, description="Number of times this card has been reviewed")
    ease_factor: float = Field(default=2.5, description="Ease factor for spaced repetition algorithm")
    interval_days: int = Field(default=1, description="Current interval in days")
    
    # Organization
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the flashcard")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata for the flashcard")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="When the card was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the card was last updated")
    
    # Statistics
    times_correct: int = Field(default=0, description="Number of times answered correctly")
    times_incorrect: int = Field(default=0, description="Number of times answered incorrectly")
    
    class Config:
        use_enum_values = True

class TwoSidedCard(BaseFlashcard):
    """Traditional flashcard with a front and back side."""
    
    type: Literal[FlashcardType.TWO_SIDED] = FlashcardType.TWO_SIDED
    front: str = Field(..., description="The question or prompt side")
    back: str = Field(..., description="The answer or response side")
    
    def get_question(self) -> str:
        """Get the question text for this card."""
        return self.front
    
    def check_answer(self, user_answer: str) -> bool:
        """Check if the user's answer is correct."""
        return user_answer.lower().strip() == self.back.lower().strip()

class FillInTheBlank(BaseFlashcard):
    """Flashcard with text containing blanks to fill in."""
    
    type: Literal[FlashcardType.FILL_IN_BLANK] = FlashcardType.FILL_IN_BLANK
    text_with_blanks: str = Field(..., description="Text with {blank} placeholders")
    answers: List[str] = Field(..., description="Correct answers for each blank")
    case_sensitive: bool = Field(default=False, description="Whether answers are case sensitive")
    
    def get_question(self) -> str:
        """Get the question text with blanks shown."""
        # Replace {blank} with _____ for display
        return self.text_with_blanks.replace("{blank}", "_____")
    
    def check_answer(self, user_answers: List[str]) -> bool:
        """Check if the user's answers are correct."""
        if len(user_answers) != len(self.answers):
            return False
        
        for user_ans, correct_ans in zip(user_answers, self.answers):
            if self.case_sensitive:
                if user_ans.strip() != correct_ans.strip():
                    return False
            else:
                if user_ans.lower().strip() != correct_ans.lower().strip():
                    return False
        return True
    
    def get_blank_count(self) -> int:
        """Get the number of blanks in this card."""
        return self.text_with_blanks.count("{blank}")

class MultipleChoice(BaseFlashcard):
    """Multiple choice flashcard with one or more correct answers."""
    
    type: Literal[FlashcardType.MULTIPLE_CHOICE] = FlashcardType.MULTIPLE_CHOICE
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="List of answer options")
    correct_indices: List[int] = Field(..., description="Indices of correct options (0-based)")
    allow_multiple: bool = Field(default=False, description="Whether multiple answers are allowed")
    
    def get_question(self) -> str:
        """Get the formatted question with options."""
        formatted_options = []
        for i, option in enumerate(self.options):
            formatted_options.append(f"{chr(65 + i)}. {option}")  # A, B, C, etc.
        
        return f"{self.question}\n\n" + "\n".join(formatted_options)
    
    def check_answer(self, selected_indices: List[int]) -> bool:
        """Check if the selected options are correct."""
        return sorted(selected_indices) == sorted(self.correct_indices)
    
    def get_correct_letters(self) -> List[str]:
        """Get the correct answer letters (A, B, C, etc.)."""
        return [chr(65 + i) for i in self.correct_indices]

# Union type for all flashcard types
FlashcardUnion = Union[TwoSidedCard, FillInTheBlank, MultipleChoice]

def create_flashcard_from_dict(data: dict) -> FlashcardUnion:
    """Create a flashcard instance from a dictionary based on its type."""
    flashcard_type = data.get("type")
    
    if flashcard_type == FlashcardType.TWO_SIDED:
        return TwoSidedCard(**data)
    elif flashcard_type == FlashcardType.FILL_IN_BLANK:
        return FillInTheBlank(**data)
    elif flashcard_type == FlashcardType.MULTIPLE_CHOICE:
        return MultipleChoice(**data)
    else:
        raise ValueError(f"Unknown flashcard type: {flashcard_type}")


class WordType(str, Enum):
    """Enum for different word types that can be processed."""
    NOUN = "noun"
    ADJECTIVE = "adjective"
    VERB = "verb"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PARTICLE = "particle"
    UNKNOWN = "unknown"


class DictionaryWord(BaseModel):
    """Model for tracking processed dictionary words to avoid regeneration."""
    
    # Identification
    id: Optional[str] = Field(None, description="Unique identifier (MongoDB ObjectId)")
    
    # Word data
    dictionary_form: str = Field(..., description="The dictionary form of the word")
    word_type: WordType = Field(..., description="Type of word (noun, verb, adjective, etc.)")
    
    # Processing metadata
    processed_date: datetime = Field(default_factory=datetime.now, description="When this word was processed")
    flashcards_generated: int = Field(default=0, description="Number of flashcards generated for this word")
    
    # Analysis metadata (optional - can store grammar analysis results)
    grammar_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cached grammar analysis data")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="When the record was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the record was last updated")
    
    class Config:
        use_enum_values = True