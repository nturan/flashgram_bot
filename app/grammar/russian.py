from pydantic import BaseModel
from typing import Literal, Dict

Case = Literal["nom", "gen", "dat", "acc", "ins", "pre"]
Gender = Literal["masculine", "feminine", "neuter"]
WordType = Literal["noun", "verb", "adjective", "adverb", "preposition", "number"]

class WordClassification(BaseModel):
    word_type: WordType
    russian_word: str
    original_word: str
    
    @staticmethod
    def get_format_instructions() -> str:
        return (
            "Your response must be valid JSON that matches this schema:\n"
            "{\n"
            "  \"word_type\": \"noun\" | \"verb\" | \"adjective\" | \"adverb\" | \"preposition\" | \"number\",\n"
            "  \"russian_word\": \"string (the Russian translation/form of the word)\",\n"
            "  \"original_word\": \"string (the original input word)\"\n"
            "}"
        )

class Noun(BaseModel):
    dictionary_form: str
    gender: Gender
    animacy: bool
    singular: Dict[Case, str]
    plural: Dict[Case, str]
    english_translation: str

    @staticmethod
    def get_format_instructions() -> str:
        return (
          "Your response must be valid JSON that matches this schema:\n"
          "{\n"
          "  \"dictionary_form\": \"string (base form of the noun)\",\n"
          "  \"gender\": \"masculine\" | \"feminine\" | \"neuter\",\n"
          "  \"animacy\": true | false,\n"
          "  \"singular\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"plural\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"english_translation\": \"string\"\n"
          "}"
        )

class Adjective(BaseModel):
    dictionary_form: str
    english_translation: str

    # Masculine forms
    masculine: Dict[Case, str]

    # Feminine forms
    feminine: Dict[Case, str]

    # Neuter forms
    neuter: Dict[Case, str]

    # Plural forms (same for all genders)
    plural: Dict[Case, str]

    # Short forms (not all adjectives have them)
    short_form_masculine: str = ""
    short_form_feminine: str = ""
    short_form_neuter: str = ""
    short_form_plural: str = ""

    # Comparative and superlative forms
    comparative: str = ""
    superlative: str = ""

    @staticmethod
    def get_format_instructions() -> str:
        return (
          "Your response must be valid JSON that matches this schema:\n"
          "{\n"
          "  \"dictionary_form\": \"string (base form of the adjective)\",\n"
          "  \"english_translation\": \"string\",\n"
          "  \"masculine\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"feminine\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"neuter\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"plural\": {\n"
          "    \"nom\": \"string\",\n"
          "    \"gen\": \"string\",\n"
          "    \"dat\": \"string\",\n"
          "    \"acc\": \"string\",\n"
          "    \"ins\": \"string\",\n"
          "    \"pre\": \"string\"\n"
          "  },\n"
          "  \"short_form_masculine\": \"string (optional)\",\n"
          "  \"short_form_feminine\": \"string (optional)\",\n"
          "  \"short_form_neuter\": \"string (optional)\",\n"
          "  \"short_form_plural\": \"string (optional)\",\n"
          "  \"comparative\": \"string (optional)\",\n"
          "  \"superlative\": \"string (optional)\"\n"
          "}"
        )

