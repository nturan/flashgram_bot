"""Conversational Russian tutor chatbot using LangGraph with tools."""

import json
import logging
from typing import List, Dict, Optional, TypedDict, Literal, Union, Any

from pydantic import SecretStr
from langgraph.graph import START, StateGraph, END
from langgraph.types import StreamWriter
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

# Import all dependencies at the top
from app.config import settings
from app.my_graph.tools import (
    analyze_russian_grammar_impl,
    correct_multilingual_mistakes_impl,
    generate_flashcards_from_analysis_impl,
    translate_phrase_impl,
    generate_example_sentences_impl,
    process_bulk_text_for_flashcards_impl,
    check_bulk_processing_status_impl,
)

logger = logging.getLogger(__name__)


class ChatbotState(TypedDict):
    """State for the conversational Russian tutor chatbot."""
    messages: List[BaseMessage]
    user_input: Optional[str]
    user_id: Optional[int]
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
        
        # Create tools from class methods
        self.tools = self._create_tools()
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the chatbot graph
        self.graph = self._build_chatbot_graph()
        
        # System message for the chatbot
        self.system_message = SystemMessage(content="""You are a helpful Russian language tutor assistant. You can help users:

1. **Analyze Russian grammar** - Break down words and explain their grammatical forms
2. **Correct mistakes** - Fix mixed-language text and grammatical errors  
3. **Generate flashcards** - Create targeted practice cards based on analysis or mistakes
4. **Process bulk text** - Handle large texts, paragraphs, or multiple sentences asynchronously
5. **Translate phrases** - Help with translations between Russian, English, and German
6. **Generate example sentences** - Create contextual examples for grammar practice

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
- Use `process_bulk_text_for_flashcards` when users provide large texts, paragraphs, multiple sentences, or lists of words:
  * This tool processes text asynchronously in the background
  * Automatically extracts Russian words and generates flashcards for each
  * Use when the text contains 4+ Russian words or when the user explicitly asks for bulk processing
  * The user_id parameter will be automatically provided
- Use `check_bulk_processing_status` to check on bulk processing jobs:
  * Use with user_id to show all jobs for a user
  * Use with job_id to check a specific job
- Use `translate_phrase` for translation requests
- Use `generate_example_sentences` when users need contextual examples

**Important tool usage notes:**
- For large texts or multiple words, prefer `process_bulk_text_for_flashcards` over individual word analysis
- When generating flashcards, you can reference previous analysis from our conversation
- If a word type isn't supported (like adverbs), explain this limitation kindly
- Always explain what you're doing and ask for user confirmation before creating flashcards
- For bulk processing, inform users that the process runs in the background and they can check the database later

Always explain what you're doing and ask for user confirmation before creating flashcards.""")

    def _create_tools(self):
        """Create tool instances from class methods."""
        
        @tool
        def analyze_russian_grammar(russian_word: str) -> Dict[str, Any]:
            """Analyze a Russian word's grammar including cases, gender, conjugations, etc.
            
            Args:
                russian_word: A single Russian word to analyze
                
            Returns:
                Dictionary with grammar analysis including word type, forms, and metadata
            """
            return analyze_russian_grammar_impl(russian_word)
        
        @tool  
        def correct_multilingual_mistakes(mixed_text: str) -> Dict[str, Any]:
            """Correct mixed-language text and grammatical mistakes in Russian.
            
            Args:
                mixed_text: Text that may contain Russian mixed with English/German words or grammatical errors
                
            Returns:
                Dictionary with original text, corrected version, and explanation of mistakes
            """
            return correct_multilingual_mistakes_impl(mixed_text)
        
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
            return generate_flashcards_from_analysis_impl(analysis_data, focus_areas, word)
        
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
            return translate_phrase_impl(text, from_lang, to_lang)
        
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
            return generate_example_sentences_impl(word, grammatical_context, theme)
        
        @tool
        def process_bulk_text_for_flashcards(text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
            """Process a large text or multiple sentences asynchronously to generate flashcards.
            
            Use this tool when the user provides:
            - Long texts or paragraphs
            - Multiple sentences
            - Lists of words
            - Any text that contains multiple Russian words to analyze
            
            This tool will automatically extract Russian words, analyze them, and generate flashcards 
            in the background. The user will be notified when processing is complete.
            
            Args:
                text: The text containing Russian words to process (can be sentences, paragraphs, or word lists)
                user_id: The user's ID for tracking the job
                
            Returns:
                Dictionary with job ID and processing information
            """
            return process_bulk_text_for_flashcards_impl(text, user_id)
        
        @tool
        def check_bulk_processing_status(job_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
            """Check the status of bulk text processing jobs.
            
            Args:
                job_id: Specific job ID to check (optional)
                user_id: User ID to get all jobs for that user (optional)
                
            Returns:
                Dictionary with job status information
            """
            return check_bulk_processing_status_impl(job_id, user_id)
        
        return [
            analyze_russian_grammar,
            generate_flashcards_from_analysis,
            correct_multilingual_mistakes,
            translate_phrase,
            generate_example_sentences,
            process_bulk_text_for_flashcards,
            check_bulk_processing_status
        ]








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
            # If there was an OpenAI API error, we need to be careful about message state
            current_messages = state.get("messages", [])
            
            # Check if the last message has tool calls that might be causing issues
            if current_messages and hasattr(current_messages[-1], 'tool_calls'):
                # Remove the problematic message that caused the error
                current_messages = current_messages[:-1]
            
            error_message = AIMessage(content="I encountered an error. Please try again.")
            return {
                **state,
                "messages": current_messages + [error_message]
            }

    def _execute_tools_node(self, state: ChatbotState) -> ChatbotState:
        """Execute any tools that were called by the AI."""
        try:
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None
            
            tool_messages = []
            
            # Validate that we have tool calls to execute
            if not last_message or not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
                logger.warning("Tool execution called but no tool calls found in last message")
                return {
                    **state,
                    "messages": messages
                }
            
            # Get user_id from state for tools that need it
            user_id = state.get("user_id")
            
            # Execute the tool calls
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]
                
                # Inject user_id for bulk processing tools
                if tool_name in ["process_bulk_text_for_flashcards", "check_bulk_processing_status"] and user_id:
                    if "user_id" not in tool_args and tool_name == "process_bulk_text_for_flashcards":
                        tool_args["user_id"] = user_id
                    elif "user_id" not in tool_args and tool_name == "check_bulk_processing_status":
                        tool_args["user_id"] = user_id
                
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
            # If there's an error during tool execution, return the state without tool messages
            # to prevent corrupting the conversation flow
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

    def chat(self, user_message: str, conversation_history: Optional[List[BaseMessage]] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Process a user message and return the chatbot's response.
        
        Args:
            user_message: The user's input message
            conversation_history: Optional previous conversation messages
            user_id: Optional user ID for tool execution context
            
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
                "user_id": user_id,
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
        self.tools = self._create_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_chatbot_graph()
        logger.info(f"Reinitialized chatbot with model: {model}")