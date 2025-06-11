"""Conversational Russian tutor chatbot using LangGraph with tools."""

from typing import List, Dict, Optional, TypedDict, Literal, Union, Any
from pydantic import SecretStr

from langgraph.graph import START, StateGraph, END
from langgraph.types import StreamWriter
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

import logging
logger = logging.getLogger(__name__)


# Define tools as standalone functions to avoid 'self' parameter issues

@tool
def analyze_russian_grammar(russian_word: str) -> Dict[str, Any]:
    """Analyze a Russian word's grammar including cases, gender, conjugations, etc.
    
    Args:
        russian_word: A single Russian word to analyze
        
    Returns:
        Dictionary with grammar analysis including word type, forms, and metadata
    """
    try:
        # Import here to avoid circular imports
        from app.my_graph.language_tutor import RussianTutor
        from app.config import settings
        
        # Create a temporary tutor instance for analysis
        # TODO: This should reuse the configured model
        temp_tutor = RussianTutor(
            api_key=SecretStr(settings.openai_api_key),
            model=settings.llm_model
        )
        
        # Run analysis without flashcard generation
        result = temp_tutor.invoke(russian_word, generate_flashcards=False)
        
        # Check if we got a classification but no grammar (e.g., unsupported word type like adverb)
        if result.get("classification") and not any([
            result.get("noun_grammar"),
            result.get("adjective_grammar"), 
            result.get("verb_grammar"),
            result.get("pronoun_grammar"),
            result.get("number_grammar")
        ]):
            word_type = result["classification"].word_type
            return {
                "word": russian_word,
                "analysis": result,
                "word_type": word_type,
                "message": f"I can identify this as a {word_type}, but detailed grammar analysis is not yet supported for this word type.",
                "success": True
            }
        
        return {
            "word": russian_word,
            "analysis": result,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in grammar analysis tool: {e}")
        return {
            "word": russian_word,
            "error": str(e),
            "success": False
        }


@tool  
def correct_multilingual_mistakes(mixed_text: str) -> Dict[str, Any]:
    """Correct mixed-language text and grammatical mistakes in Russian.
    
    Args:
        mixed_text: Text that may contain Russian mixed with English/German words or grammatical errors
        
    Returns:
        Dictionary with original text, corrected version, and explanation of mistakes
    """
    try:
        from app.config import settings
        
        # Create LLM instance
        llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        
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
        import json
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
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Error in correction tool: {e}")
        return {
            "original": mixed_text,
            "error": str(e),
            "success": False
        }


@tool
def generate_flashcards_from_analysis(analysis_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None, 
                                    focus_areas: Optional[List[str]] = None,
                                    word: Optional[str] = None) -> Dict[str, Any]:
    """Generate flashcards from grammar analysis results.
    
    Args:
        analysis_data: Results from grammar analysis (optional if word is provided)
        focus_areas: Optional list of specific areas to focus on (e.g., ['cases', 'gender'])
        word: Optional word to analyze if analysis_data not provided
        
    Returns:
        Dictionary with generated flashcards and count
    """
    try:
        # Import here to avoid circular imports
        from app.my_graph.flashcard_generator import flashcard_generator
        import json
        
        # Handle case where analysis_data is a list (multiple words analyzed)
        if isinstance(analysis_data, list):
            if len(analysis_data) == 1:
                analysis_data = analysis_data[0]
            else:
                # For multiple words, generate flashcards for all and combine results
                total_flashcards = 0
                combined_word_types = []
                
                for single_analysis in analysis_data:
                    result = generate_flashcards_from_analysis(single_analysis, focus_areas, None)
                    if result.get("success"):
                        total_flashcards += result.get("flashcards_generated", 0)
                        if result.get("word_type"):
                            combined_word_types.append(result["word_type"])
                
                return {
                    "flashcards_generated": total_flashcards,
                    "total_flashcards": total_flashcards,
                    "word_types": combined_word_types,
                    "focus_areas": focus_areas,
                    "message": f"Generated {total_flashcards} flashcards for {len(analysis_data)} words",
                    "success": True
                }

        # If no analysis_data provided but word is given, analyze the word first
        if not analysis_data and word:
            analysis_result = analyze_russian_grammar(word)
            if analysis_result.get("success"):
                analysis_data = analysis_result
        
        # Extract grammar analysis from the tool result
        grammar_result = None
        if analysis_data and "analysis" in analysis_data:
            grammar_result = analysis_data["analysis"]
        elif analysis_data and any(key in analysis_data for key in ["noun_grammar", "adjective_grammar", "verb_grammar", "pronoun_grammar", "number_grammar"]):
            # analysis_data might be the grammar_result itself
            grammar_result = analysis_data
        
        if grammar_result:
            # Determine word type and grammar object
            flashcards = []
            word_type = None
            grammar_obj = None
            
            if grammar_result.get("noun_grammar"):
                grammar_data = grammar_result["noun_grammar"]
                word_type = "noun"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Noun
                    grammar_obj = Noun(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("adjective_grammar"):
                grammar_data = grammar_result["adjective_grammar"]
                word_type = "adjective"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Adjective
                    grammar_obj = Adjective(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("verb_grammar"):
                grammar_data = grammar_result["verb_grammar"]
                word_type = "verb"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Verb
                    grammar_obj = Verb(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("pronoun_grammar"):
                grammar_data = grammar_result["pronoun_grammar"]
                word_type = "pronoun"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Pronoun
                    grammar_obj = Pronoun(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("number_grammar"):
                grammar_data = grammar_result["number_grammar"]
                word_type = "number"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Number as NumberClass
                    grammar_obj = NumberClass(**grammar_data)
                else:
                    grammar_obj = grammar_data
            
            if grammar_obj and word_type:
                # Generate flashcards
                flashcards = flashcard_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type
                )
                
                # Save to database
                saved_count = flashcard_generator.save_flashcards_to_database(flashcards)
                
                # Track dictionary word only if flashcards were generated successfully
                if saved_count > 0 and grammar_obj:
                    # Extract dictionary form from grammar object
                    dictionary_form = getattr(grammar_obj, 'dictionary_form', None)
                    if dictionary_form:
                        from app.flashcards import flashcard_service
                        from app.flashcards.models import WordType
                        
                        try:
                            word_type_enum = WordType(word_type)
                            
                            # Check if word already exists in dictionary
                            existing_word = flashcard_service.db.get_processed_word(dictionary_form, word_type_enum)
                            if existing_word:
                                # Update existing word stats
                                flashcard_service.db.update_processed_word_stats(
                                    dictionary_form, word_type_enum, additional_flashcards=saved_count
                                )
                                logger.info(f"Updated stats for existing word {dictionary_form} (+{saved_count} flashcards)")
                            else:
                                # Add new processed word
                                flashcard_service.db.add_processed_word(
                                    dictionary_form=dictionary_form,
                                    word_type=word_type_enum,
                                    flashcards_generated=saved_count,
                                    grammar_data=grammar_result
                                )
                                logger.info(f"Added new word {dictionary_form} to dictionary with {saved_count} flashcards")
                        except ValueError:
                            logger.warning(f"Word type {word_type} not supported for dictionary tracking")
                
                focus_info = f" (focusing on {', '.join(focus_areas)})" if focus_areas else ""
                
                return {
                    "flashcards_generated": saved_count,
                    "total_flashcards": len(flashcards),
                    "word_type": word_type,
                    "focus_areas": focus_areas,
                    "message": f"Generated {saved_count} flashcards for {word_type}{focus_info}",
                    "success": True
                }
            else:
                # Word type not supported for flashcard generation
                return {
                    "flashcards_generated": 0,
                    "error": f"Flashcard generation not supported for this word type",
                    "success": False
                }
        
        return {
            "flashcards_generated": 0,
            "error": "No valid grammar analysis found. Please provide analysis_data or word parameter.",
            "success": False
        }
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return {
            "flashcards_generated": 0,
            "error": str(e),
            "success": False
        }


@tool
def translate_phrase(text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
    """Translate a phrase between Russian, English, and German.
    
    Args:
        text: Text to translate
        from_lang: Source language (russian, english, german)
        to_lang: Target language (russian, english, german)
        
    Returns:
        Dictionary with translation and additional context
    """
    try:
        from app.config import settings
        
        # Create LLM instance
        llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        
        translation_prompt = f"""Translate the following {from_lang} text to {to_lang}:

Text: "{text}"

Provide a natural, contextually appropriate translation. If the text contains grammar learning content, include brief notes about any important grammatical considerations."""

        response = llm.invoke([HumanMessage(content=translation_prompt)])
        
        return {
            "original": text,
            "translation": response.content,
            "from_language": from_lang,
            "to_language": to_lang,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in translation tool: {e}")
        return {
            "original": text,
            "error": str(e),
            "success": False
        }


@tool
def generate_example_sentences(word: str, grammatical_context: str, theme: Optional[str] = None) -> Dict[str, Any]:
    """Generate example sentences for a Russian word in specific grammatical contexts.
    
    Args:
        word: Russian word to create examples for
        grammatical_context: Grammar context (e.g., "accusative case", "past tense")
        theme: Optional theme for examples (e.g., "family", "cooking", "travel")
        
    Returns:
        Dictionary with generated example sentences
    """
    try:
        # Import here to avoid circular imports
        from app.my_graph.sentence_generation import LLMSentenceGenerator
        
        sentence_generator = LLMSentenceGenerator()
        
        examples = []
        
        # Generate 2-3 example sentences
        for i in range(3):
            if theme:
                sentence = sentence_generator.generate_contextual_sentence(
                    word, word, grammatical_context, theme
                )
            else:
                sentence = sentence_generator.generate_example_sentence(
                    word, word, grammatical_context, "word"
                )
            examples.append(sentence)
        
        return {
            "word": word,
            "context": grammatical_context,
            "theme": theme,
            "examples": examples,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error generating example sentences: {e}")
        return {
            "word": word,
            "error": str(e),
            "success": False
        }


class ChatbotState(TypedDict):
    """State for the conversational Russian tutor chatbot."""
    messages: List[BaseMessage]
    user_input: Optional[str]
    # Tool execution results
    tool_results: Optional[Dict[str, Any]]
    # Context for ongoing tasks
    current_analysis: Optional[Dict[str, Any]]
    pending_flashcards: Optional[List[Any]]
    conversation_context: Optional[Dict[str, Any]]


class ConversationalRussianTutor:
    """A conversational Russian tutor chatbot using LangGraph with tools."""
    
    def __init__(self, api_key: SecretStr, model: str = "gpt-4o"):
        self.api_key = api_key
        self.default_model = model
        
        # Create LLM with tool binding
        self.llm = ChatOpenAI(api_key=api_key, model=model)
        
        # Define tools (using standalone functions)
        self.tools = [
            analyze_russian_grammar,
            generate_flashcards_from_analysis,
            correct_multilingual_mistakes,
            translate_phrase,
            generate_example_sentences
        ]
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the chatbot graph
        self.graph = self._build_chatbot_graph()
        
        # System message for the chatbot
        self.system_message = SystemMessage(content="""You are a helpful Russian language tutor assistant. You can help users:

1. **Analyze Russian grammar** - Break down words and explain their grammatical forms
2. **Correct mistakes** - Fix mixed-language text and grammatical errors  
3. **Generate flashcards** - Create targeted practice cards based on analysis or mistakes
4. **Translate phrases** - Help with translations between Russian, English, and German
5. **Generate example sentences** - Create contextual examples for grammar practice

**Your personality:**
- Encouraging and patient with learners
- Explain grammar concepts clearly
- Ask clarifying questions when needed
- Offer to create flashcards when it would help learning
- Respond naturally in conversation

**When to use tools:**
- Use `analyze_russian_grammar` for single Russian words or when detailed grammar analysis is requested
- Use `correct_multilingual_mistakes` when users send mixed-language or incorrect Russian text
- Use `generate_flashcards_from_analysis` when users want practice cards created:
  * If you have recent analysis results, pass them as `analysis_data`
  * If you don't have analysis results, just pass the `word` parameter
  * You can specify `focus_areas` like ["cases", "tenses", "gender"] if user mentions specific interests
- Use `translate_phrase` for translation requests
- Use `generate_example_sentences` when users need contextual examples

**Important tool usage notes:**
- When generating flashcards, you can reference previous analysis from our conversation
- If a word type isn't supported (like adverbs), explain this limitation kindly
- Always explain what you're doing and ask for user confirmation before creating flashcards

Always explain what you're doing and ask for user confirmation before creating flashcards.""")

    def _build_chatbot_graph(self) -> Any:
        """Build the LangGraph for the conversational chatbot."""
        
        workflow = StateGraph(ChatbotState)
        
        # Main chat node
        workflow.add_node("chat", self._chat_node)
        
        # Tool execution nodes
        workflow.add_node("execute_tools", self._execute_tools_node)
        
        # Start with chat
        workflow.add_edge(START, "chat")
        
        # Route from chat based on whether tools were called
        workflow.add_conditional_edges(
            "chat",
            self._should_execute_tools,
            {
                "tools": "execute_tools",
                "respond": END
            }
        )
        
        # After tools, go back to chat to respond
        workflow.add_edge("execute_tools", "chat")
        
        return workflow.compile()

    def _chat_node(self, state: ChatbotState) -> ChatbotState:
        """Main chat node that handles conversation and tool calling."""
        try:
            messages = state.get("messages", [])
            
            # Add system message if this is the start of conversation
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [self.system_message] + messages
            
            # Get AI response
            response = self.llm_with_tools.invoke(messages)
            
            # Add the response to messages
            updated_messages = messages + [response]
            
            return {
                **state,
                "messages": updated_messages
            }
            
        except Exception as e:
            logger.error(f"Error in chat node: {e}")
            error_message = AIMessage(content="I encountered an error. Please try again.")
            return {
                **state,
                "messages": state.get("messages", []) + [error_message]
            }

    def _execute_tools_node(self, state: ChatbotState) -> ChatbotState:
        """Execute any tools that were called by the AI."""
        try:
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None
            
            tool_messages = []
            
            if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    # Find and execute the tool
                    tool_result = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            try:
                                tool_result = tool.invoke(tool_args)
                                logger.info(f"Executed tool {tool_name} with result: {tool_result}")
                            except Exception as e:
                                logger.error(f"Error executing tool {tool_name}: {e}")
                                tool_result = {"error": str(e), "success": False}
                            break
                    
                    if tool_result is None:
                        tool_result = {"error": f"Tool {tool_name} not found", "success": False}
                    
                    # Create a ToolMessage with the result
                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    )
                    tool_messages.append(tool_message)
            
            # Add tool messages to the conversation
            updated_messages = messages + tool_messages
            
            return {
                **state,
                "messages": updated_messages,
                "tool_results": {msg.tool_call_id: msg.content for msg in tool_messages}
            }
            
        except Exception as e:
            logger.error(f"Error in execute tools node: {e}")
            return {
                **state,
                "tool_results": {"error": str(e)}
            }

    def _should_execute_tools(self, state: ChatbotState) -> str:
        """Determine if we should execute tools or respond directly."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if (last_message and 
            hasattr(last_message, 'tool_calls') and 
            last_message.tool_calls):
            return "tools"
        return "respond"

    def chat(self, user_message: str, conversation_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """Process a user message and return the chatbot's response.
        
        Args:
            user_message: The user's input message
            conversation_history: Optional previous conversation messages
            
        Returns:
            Dictionary with the AI's response and updated conversation state
        """
        try:
            # Prepare initial state
            messages = conversation_history or []
            messages.append(HumanMessage(content=user_message))
            
            initial_state = {
                "messages": messages,
                "user_input": user_message,
                "tool_results": None,
                "current_analysis": None,
                "pending_flashcards": None,
                "conversation_context": None
            }
            
            # Execute the graph
            result = self.graph.invoke(initial_state)
            
            # Extract the final AI response
            final_messages = result.get("messages", [])
            ai_response = ""
            
            if final_messages:
                last_message = final_messages[-1]
                if isinstance(last_message, AIMessage):
                    ai_response = last_message.content
            
            return {
                "response": ai_response,
                "messages": final_messages,
                "tool_results": result.get("tool_results"),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in chat method: {e}")
            return {
                "response": "I encountered an error processing your message. Please try again.",
                "messages": conversation_history or [],
                "error": str(e),
                "success": False
            }

    def reinit_with_model(self, model: str):
        """Reinitialize the chatbot with a new model."""
        self.llm = ChatOpenAI(api_key=self.api_key, model=model)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_chatbot_graph()
        logger.info(f"Reinitialized chatbot with model: {model}")