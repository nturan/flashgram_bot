from pydantic import BaseModel
from typing import Literal, Dict, Optional

Case = Literal["nom", "gen", "dat", "acc", "ins", "pre"]
Gender = Literal["masculine", "feminine", "neuter"]
WordType = Literal["noun", "verb", "adjective", "adverb", "preposition", "number", "pronoun"]
Aspect = Literal["perfective", "imperfective", "both"]
Person = Literal["first", "second", "third"]
Number = Literal["singular", "plural"]
Tense = Literal["present", "past", "future"]
Mood = Literal["indicative", "imperative", "conditional"]

class WordClassification(BaseModel):
    word_type: WordType
    russian_word: str
    original_word: str
    
    @staticmethod
    def get_format_instructions() -> str:
        return (
            "Your response must be valid JSON that matches this schema:\n"
            "{\n"
            "  \"word_type\": \"noun\" | \"verb\" | \"adjective\" | \"adverb\" | \"preposition\" | \"number\" | \"pronoun\",\n"
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

class Verb(BaseModel):
    dictionary_form: str
    english_translation: str
    aspect: Aspect
    aspect_pair: Optional[str] = None  # The verb's aspectual partner (if it exists)
    
    # Motion verb characteristics
    unidirectional: bool = False  # For motion verbs like идти vs ехать
    multidirectional: bool = False  # For motion verbs like ходить vs ездить
    
    # Conjugation pattern (1st or 2nd conjugation)
    conjugation: Literal["first", "second", "irregular"]
    
    # Present tense forms (only for imperfective verbs)
    present_first_singular: Optional[str] = None
    present_second_singular: Optional[str] = None
    present_third_singular: Optional[str] = None
    present_first_plural: Optional[str] = None
    present_second_plural: Optional[str] = None
    present_third_plural: Optional[str] = None
    
    # Past tense forms
    past_masculine: str
    past_feminine: str  
    past_neuter: str
    past_plural: str
    
    # Future tense forms (for perfective verbs, or будущее сложное for imperfective)
    future_first_singular: Optional[str] = None
    future_second_singular: Optional[str] = None
    future_third_singular: Optional[str] = None
    future_first_plural: Optional[str] = None
    future_second_plural: Optional[str] = None
    future_third_plural: Optional[str] = None
    
    # Imperative forms
    imperative_singular: Optional[str] = None
    imperative_plural: Optional[str] = None
    
    # Participles and gerunds (optional)
    present_active_participle: Optional[str] = None
    present_passive_participle: Optional[str] = None
    past_active_participle: Optional[str] = None
    past_passive_participle: Optional[str] = None
    present_gerund: Optional[str] = None
    past_gerund: Optional[str] = None

    @staticmethod
    def get_format_instructions() -> str:
        return (
            "Your response must be valid JSON that matches this schema:\n"
            "{\n"
            "  \"dictionary_form\": \"string (infinitive form of the verb)\",\n"
            "  \"english_translation\": \"string\",\n"
            "  \"aspect\": \"perfective\" | \"imperfective\" | \"both\",\n"
            "  \"aspect_pair\": \"string or null (the aspectual partner verb if it exists)\",\n"
            "  \"unidirectional\": true | false,\n"
            "  \"multidirectional\": true | false,\n"
            "  \"conjugation\": \"first\" | \"second\" | \"irregular\",\n"
            "  \"present_first_singular\": \"string or null (я form, only for imperfective verbs)\",\n"
            "  \"present_second_singular\": \"string or null (ты form, only for imperfective verbs)\",\n"
            "  \"present_third_singular\": \"string or null (он/она/оно form, only for imperfective verbs)\",\n"
            "  \"present_first_plural\": \"string or null (мы form, only for imperfective verbs)\",\n"
            "  \"present_second_plural\": \"string or null (вы form, only for imperfective verbs)\",\n"
            "  \"present_third_plural\": \"string or null (они form, only for imperfective verbs)\",\n"
            "  \"past_masculine\": \"string (он form)\",\n"
            "  \"past_feminine\": \"string (она form)\",\n"
            "  \"past_neuter\": \"string (оно form)\",\n"
            "  \"past_plural\": \"string (они form)\",\n"
            "  \"future_first_singular\": \"string or null (я form, for perfective or compound future)\",\n"
            "  \"future_second_singular\": \"string or null (ты form, for perfective or compound future)\",\n"
            "  \"future_third_singular\": \"string or null (он/она/оно form, for perfective or compound future)\",\n"
            "  \"future_first_plural\": \"string or null (мы form, for perfective or compound future)\",\n"
            "  \"future_second_plural\": \"string or null (вы form, for perfective or compound future)\",\n"
            "  \"future_third_plural\": \"string or null (они form, for perfective or compound future)\",\n"
            "  \"imperative_singular\": \"string or null (imperative singular form if exists)\",\n"
            "  \"imperative_plural\": \"string or null (imperative plural form if exists)\",\n"
            "  \"present_active_participle\": \"string or null (if exists)\",\n"
            "  \"present_passive_participle\": \"string or null (if exists)\",\n"
            "  \"past_active_participle\": \"string or null (if exists)\",\n"
            "  \"past_passive_participle\": \"string or null (if exists)\",\n"
            "  \"present_gerund\": \"string or null (if exists)\",\n"
            "  \"past_gerund\": \"string or null (if exists)\"\n"
            "}\n"
            "Important: Use null for optional fields that don't exist or don't apply to this verb."
        )


class Pronoun(BaseModel):
    dictionary_form: str
    english_translation: str
    pronoun_type: Literal["personal", "possessive", "demonstrative", "interrogative", "relative", "indefinite", "negative"]
    
    # Person and number (for personal pronouns)
    person: Optional[Person] = None
    number: Optional[Number] = None
    
    # Gender (some pronouns have gender, like он/она/оно)
    gender: Optional[Gender] = None
    
    # Declension pattern - some pronouns decline like nouns, others like adjectives
    declension_pattern: Literal["noun_like", "adjective_like", "special"]
    
    # Declensions - structure depends on the pattern
    # For personal pronouns (noun-like): simple case forms
    singular: Optional[Dict[Case, str]] = None
    plural: Optional[Dict[Case, str]] = None
    
    # For adjective-like pronouns: gender-specific forms
    masculine: Optional[Dict[Case, str]] = None
    feminine: Optional[Dict[Case, str]] = None
    neuter: Optional[Dict[Case, str]] = None
    plural_adjective_like: Optional[Dict[Case, str]] = None
    
    # Special notes for irregular pronouns
    notes: Optional[str] = None

    @staticmethod
    def get_format_instructions() -> str:
        return (
            "Your response must be valid JSON that matches this schema:\n"
            "{\n"
            "  \"dictionary_form\": \"string (base form of the pronoun)\",\n"
            "  \"english_translation\": \"string\",\n"
            "  \"pronoun_type\": \"personal\" | \"possessive\" | \"demonstrative\" | \"interrogative\" | \"relative\" | \"indefinite\" | \"negative\",\n"
            "  \"person\": \"first\" | \"second\" | \"third\" | null,\n"
            "  \"number\": \"singular\" | \"plural\" | null,\n"
            "  \"gender\": \"masculine\" | \"feminine\" | \"neuter\" | null,\n"
            "  \"declension_pattern\": \"noun_like\" | \"adjective_like\" | \"special\",\n"
            "  \"singular\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"plural\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"masculine\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"feminine\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"neuter\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"plural_adjective_like\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"notes\": \"string | null (special notes for irregular pronouns)\"\n"
            "}\n"
            "Important: Use appropriate declension pattern:\n"
            "- noun_like: for personal pronouns (я, ты, он, она, оно, мы, вы, они) - use singular/plural fields\n"
            "- adjective_like: for demonstrative, possessive pronouns (этот, мой, наш) - use masculine/feminine/neuter/plural_adjective_like fields\n"
            "- special: for irregular pronouns with unique declension patterns"
        )


class Number(BaseModel):
    dictionary_form: str
    english_translation: str
    numeric_value: int  # The actual number (1, 2, 3, etc.)
    number_type: Literal["cardinal", "ordinal", "collective"]
    
    # Number category affects declension pattern
    number_category: Literal[
        "one",           # один/одна/одно (declines like adjective)
        "two_three_four", # два/три/четыре (special pattern)
        "five_twenty",   # пять-двадцать (like feminine nouns ending in ь)
        "tens",          # тридцать, сорок, etc. (special patterns)
        "hundreds",      # сто, двести, триста, etc. (special patterns)
        "thousands",     # тысяча (like feminine noun)
        "compound",      # compound numbers (двадцать один, etc.)
        "special"        # irregular numbers
    ]
    
    # Gender (for числительные that have gender like один/одна/одно)
    gender: Optional[Gender] = None
    
    # Declension patterns vary by category
    # For "one" type - adjective-like declension with gender
    masculine: Optional[Dict[Case, str]] = None
    feminine: Optional[Dict[Case, str]] = None
    neuter: Optional[Dict[Case, str]] = None
    
    # For most other numbers - simpler case forms
    singular: Optional[Dict[Case, str]] = None
    plural: Optional[Dict[Case, str]] = None
    
    # Special case forms for compound numbers
    compound_forms: Optional[Dict[str, str]] = None
    
    # Usage notes for complex numbers
    usage_notes: Optional[str] = None
    
    # Agreement patterns (what case the counted noun takes)
    noun_agreement: Optional[Dict[Case, str]] = None

    @staticmethod
    def get_format_instructions() -> str:
        return (
            "Your response must be valid JSON that matches this schema:\n"
            "{\n"
            "  \"dictionary_form\": \"string (base form of the number)\",\n"
            "  \"english_translation\": \"string\",\n"
            "  \"numeric_value\": number (1, 2, 3, etc.),\n"
            "  \"number_type\": \"cardinal\" | \"ordinal\" | \"collective\",\n"
            "  \"number_category\": \"one\" | \"two_three_four\" | \"five_twenty\" | \"tens\" | \"hundreds\" | \"thousands\" | \"compound\" | \"special\",\n"
            "  \"gender\": \"masculine\" | \"feminine\" | \"neuter\" | null,\n"
            "  \"masculine\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"feminine\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"neuter\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"singular\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"plural\": {\n"
            "    \"nom\": \"string\",\n"
            "    \"gen\": \"string\",\n"
            "    \"dat\": \"string\",\n"
            "    \"acc\": \"string\",\n"
            "    \"ins\": \"string\",\n"
            "    \"pre\": \"string\"\n"
            "  } | null,\n"
            "  \"compound_forms\": object | null,\n"
            "  \"usage_notes\": \"string | null\",\n"
            "  \"noun_agreement\": {\n"
            "    \"nom\": \"string (what case nouns take when number is nominative)\",\n"
            "    \"gen\": \"string (what case nouns take when number is genitive)\",\n"
            "    \"dat\": \"string (what case nouns take when number is dative)\",\n"
            "    \"acc\": \"string (what case nouns take when number is accusative)\",\n"
            "    \"ins\": \"string (what case nouns take when number is instrumental)\",\n"
            "    \"pre\": \"string (what case nouns take when number is prepositional)\"\n"
            "  } | null\n"
            "}\n"
            "Important: Choose the correct category and use appropriate fields:\n"
            "- 'one': один/одна/одно - use masculine/feminine/neuter fields (adjective-like)\n"
            "- 'two_three_four': два, три, четыре - use singular field\n"
            "- 'five_twenty': пять-двадцать - use singular field\n"
            "- 'tens': тридцать, сорок, пятьдесят-девяносто - use singular field\n"
            "- 'hundreds': сто, двести, триста-девятьсот - use singular field\n"
            "- 'thousands': тысяча, миллион, etc. - use singular/plural fields\n"
            "- 'compound': complex numbers like двадцать один - use compound_forms\n"
            "Include noun_agreement patterns using short case names (nom/gen/dat/acc/ins/pre):\n"
            "- For 2-4: usually genitive singular for counted nouns\n"
            "- For 5+: usually genitive plural for counted nouns\n"
            "Example: {\"nom\": \"genitive_singular\", \"gen\": \"genitive_singular\", ...}\""
        )

