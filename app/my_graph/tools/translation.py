"""Translation tool implementation."""

import logging
from typing import Dict, Any

from pydantic import SecretStr
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def translate_phrase_impl(text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
    """Implementation for translation tool."""
    try:
        # Create LLM instance
        llm = ChatOpenAI(
            api_key=SecretStr(settings.openai_api_key), model=settings.llm_model
        )

        translation_prompt = f"""Translate the following {from_lang} text to {to_lang}:

Text: "{text}"

Provide a natural, contextually appropriate translation. If the text contains grammar learning content, include brief notes about any important grammatical considerations."""

        response = llm.invoke([HumanMessage(content=translation_prompt)])

        return {
            "original": text,
            "translation": response.content,
            "from_language": from_lang,
            "to_language": to_lang,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error in translation tool: {e}")
        return {"original": text, "error": str(e), "success": False}