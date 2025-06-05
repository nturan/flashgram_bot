from pydantic import BaseModel
from typing import Literal, Dict

Case = Literal["nom", "gen", "dat", "acc", "ins", "pre"]

class Noun(BaseModel):
    dictionary_form: str
    gender: Literal["masculine", "feminine", "neuter"]
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

