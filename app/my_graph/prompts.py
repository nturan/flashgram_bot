from langchain_core.prompts import ChatPromptTemplate
from app.grammar.russian import (
  Noun,
  Adjective,
  Verb,
  Pronoun,
  Number,
  WordClassification
)


initial_classification_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a word in english, german, turkish, azerbaijani or russian."
       "If the word is in russian find its dictionary form and classify it as a noun, number, verb, adjective, adverb, preposition, or pronoun."
       "If the word is in any other language, translate it to russian and classify it as a noun, number, verb, adjective, adverb, preposition, or pronoun."
       "\nIMPORTANT: Pay special attention to NUMBERS (числительные):"
       "\n- Cardinal numbers: один/одна/одно, два, три, четыре, пять, шесть, семь, восемь, девять, десять, одиннадцать, двенадцать, тринадцать, четырнадцать, пятнадцать, шестнадцать, семнадцать, восемнадцать, девятнадцать, двадцать, тридцать, сорок, пятьдесят, шестьдесят, семьдесят, восемьдесят, девяносто, сто, двести, триста, четыреста, пятьсот, шестьсот, семьсот, восемьсот, девятьсот, тысяча, миллион, миллиард"
       "\n- Ordinal numbers: первый, второй, третий, четвёртый, пятый, etc."
       "\n- Collective numbers: двое, трое, четверо, пятеро, etc."
       "\nEven if a number behaves grammatically like an adjective or noun, it should still be classified as 'number'."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}")
  ],
  partial_variables={
    "format_instructions": WordClassification.get_format_instructions(),
  }
)

get_noun_grammar_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a noun in russian."
       "If the word is a noun, find its dictionary form and classify it as masculine, feminine or neuter."
       "Also find its animacy and singular and plural forms in all cases."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}"),
  ],
  partial_variables={
    "format_instructions": Noun.get_format_instructions(),
  }
)

get_adjective_grammar_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given an adjective in russian."
       "Find its dictionary form and provide all its forms for masculine, feminine, neuter, and plural in all cases."
       "If available, also provide the short forms, comparative form, and superlative form."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}"),
  ],
  partial_variables={
    "format_instructions": Adjective.get_format_instructions(),
  }
)

get_verb_grammar_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a verb in russian."
       "Find its dictionary form (infinitive) and provide its aspect (perfective/imperfective), aspect pair if it exists, "
       "conjugation pattern, and all conjugated forms including present (for imperfective), past, future, imperative forms. "
       "For motion verbs, indicate if they are unidirectional or multidirectional. "
       "Also include participles and gerunds if they exist."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}"),
  ],
  partial_variables={
    "format_instructions": Verb.get_format_instructions(),
  }
)

get_pronoun_grammar_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a pronoun in russian."
       "Find its dictionary form and identify its type (personal, possessive, demonstrative, interrogative, relative, indefinite, or negative). "
       "Determine its declension pattern and provide all case forms. "
       "For personal pronouns (я, ты, он, она, оно, мы, вы, они), use the noun-like pattern with singular/plural fields. "
       "For demonstrative and possessive pronouns (этот, мой, наш, etc.), use the adjective-like pattern with masculine/feminine/neuter/plural fields. "
       "Include person, number, and gender information where applicable."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}"),
  ],
  partial_variables={
    "format_instructions": Pronoun.get_format_instructions(),
  }
)

get_number_grammar_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a number in russian (cardinal, ordinal, or collective)."
       "Find its dictionary form, numeric value, and determine its type and category. "
       "Provide all case forms according to the number's declension pattern. "
       "For 'один/одна/одно' use adjective-like declension with masculine/feminine/neuter fields. "
       "For 'два/три/четыре' and 'пять-двадцать' use singular case forms. "
       "For compound numbers include special compound forms. "
       "Include noun agreement patterns (what case the counted noun takes with this number). "
       "Specify usage notes for irregular or complex numbers."
       "\nYour response MUST be a valid JSON object matching this schema:\n"
       "{format_instructions}\n"
     )),
    ("user", "{word}"),
  ],
  partial_variables={
    "format_instructions": Number.get_format_instructions(),
  }
)