"""Text correction tool implementation."""

import json
import logging
from typing import Dict, Any

from pydantic import SecretStr
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def correct_multilingual_mistakes_impl(mixed_text: str) -> Dict[str, Any]:
    """Implementation for correction tool."""
    try:
        # Create LLM instance
        llm = ChatOpenAI(
            api_key=SecretStr(settings.openai_api_key), model=settings.llm_model
        )

        correction_prompt = f"""Please analyze and correct this text that is intended to be Russian but may contain foreign words or grammatical mistakes:

Text: "{mixed_text}"

Provide a response in the following JSON format:
{{
    "original": "{mixed_text}",
    "corrected": "grammatically correct Russian version",
    "mistakes": [
        {{
            "type": "foreign_word|grammar|case|gender|spelling",
            "original": "incorrect part",
            "corrected": "correct version", 
            "explanation": "brief explanation of the mistake"
        }}
    ],
    "overall_explanation": "brief summary of what was corrected"
}}

Focus on:
1. Replacing English/German words with Russian equivalents
2. Fixing case agreements (noun-adjective, preposition-noun)
3. Correcting verb conjugations
4. Fixing word order if needed
"""

        response = llm.invoke([HumanMessage(content=correction_prompt)])

        # Try to parse JSON response
        try:
            result = json.loads(response.content)
            result["success"] = True
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "original": mixed_text,
                "corrected": response.content,
                "mistakes": [],
                "overall_explanation": "Correction provided but couldn't parse detailed breakdown",
                "success": True,
            }

    except Exception as e:
        logger.error(f"Error in correction tool: {e}")
        return {"original": mixed_text, "error": str(e), "success": False}