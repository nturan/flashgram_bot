from langchain_core.prompts import ChatPromptTemplate
from app.grammar.russian import (
  Noun,
  Adjective
)


initial_classification_prompt = ChatPromptTemplate(
  messages=[
    ("system",
     (
       "You are a helpful assistant that helps the user to learn russian."
       "You will be given a word in english, german, turkish, azerbaijani or russian."
       "If the word is in russian find its dictionary form and classify it as a noun, number, verb, adjective, adverb or preposition."
       "If the word is in any other language, translate it to russian and classify it as a noun, number, verb, adjective, adverb or preposition."
     )),
    ("user", "{word}")
  ]
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