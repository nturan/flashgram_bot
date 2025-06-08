from typing import List, Dict, Optional, TypedDict, Literal, Union, Any
from pydantic import SecretStr

from langgraph.graph import START, StateGraph, END
from langgraph.types import interrupt, Command, StreamWriter
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig, RunnableLambda, RunnableSerializable
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.my_graph.prompts import (
  initial_classification_prompt,
  get_noun_grammar_prompt,
  get_adjective_grammar_prompt,
  get_verb_grammar_prompt,
)
from app.grammar.russian import (
  WordClassification,
  Noun,
  Adjective,
  Verb,
)
from app.my_graph.flashcard_generator import flashcard_generator

class State(TypedDict):
    original_human_input: str
    classification: Optional[WordClassification]
    noun_grammar: Optional[Noun]
    adjective_grammar: Optional[Adjective]
    verb_grammar: Optional[Verb]
    final_answer: Optional[str]
    generate_flashcards: Optional[bool]
    flashcards_generated: Optional[int]
    flashcard_generation_message: Optional[str]


class RussianTutor:
    def __init__(self, api_key: SecretStr, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(api_key=api_key, model=model)

        self.initial_classification_chain = (
            initial_classification_prompt
            | self.llm
            | PydanticOutputParser(pydantic_object=WordClassification)
        )

        self.get_noun_grammar_chain: RunnableSerializable[dict[Any, Any], Noun] = (
            get_noun_grammar_prompt
            | self.llm
            | PydanticOutputParser(pydantic_object=Noun)
        )

        self.get_adjective_grammar_chain: RunnableSerializable[dict[Any, Any], Adjective] = (
            get_adjective_grammar_prompt
            | self.llm
            | PydanticOutputParser(pydantic_object=Adjective)
        )

        self.get_verb_grammar_chain: RunnableSerializable[dict[Any, Any], Verb] = (
            get_verb_grammar_prompt
            | self.llm
            | PydanticOutputParser(pydantic_object=Verb)
        )

        self.graph = self._build_graph()

    def initial_classification(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Classify the input word and determine its part of speech"""
        if writer and hasattr(writer, 'write'):
            writer.write("Analyzing input...\n")

        result: WordClassification = self.initial_classification_chain.invoke(
            {"word": state["original_human_input"]},
            config=config
        )

        return {
            **state,
            "classification": result
        }

    def get_noun_grammar(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Get grammar details for a Russian noun"""
        if writer and hasattr(writer, 'write'):
            writer.write("Getting noun grammar details...\n")

        word = state.get("classification").russian_word if state.get("classification") else state["original_human_input"]

        result: Noun = self.get_noun_grammar_chain.invoke(
            {"word": word}, config=config
        )

        return {
            **state,
            "noun_grammar": result,
            "final_answer": result.model_dump_json(indent=2)
        }

    def get_adjective_grammar(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Get grammar details for a Russian adjective"""
        if writer and hasattr(writer, 'write'):
            writer.write("Getting adjective grammar details...\n")

        word = state.get("classification").russian_word if state.get("classification") else state["original_human_input"]

        result: Adjective = self.get_adjective_grammar_chain.invoke(
            {"word": word}, config=config
        )

        return {
            **state,
            "adjective_grammar": result,
            "final_answer": result.model_dump_json(indent=2)
        }

    def get_verb_grammar(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Get grammar details for a Russian verb"""
        if writer and hasattr(writer, 'write'):
            writer.write("Getting verb grammar details...\n")

        word = state.get("classification").russian_word if state.get("classification") else state["original_human_input"]

        result: Verb = self.get_verb_grammar_chain.invoke(
            {"word": word}, config=config
        )

        return {
            **state,
            "verb_grammar": result,
            "final_answer": result.model_dump_json(indent=2)
        }

    def generate_flashcards(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Generate flashcards from the grammar analysis results."""
        if writer and hasattr(writer, 'write'):
            writer.write("Generating flashcards...\n")

        try:
            flashcards = []
            word_type = None
            grammar_obj = None
            
            # Determine which grammar object to use
            if state.get("noun_grammar"):
                grammar_obj = state["noun_grammar"]
                word_type = "noun"
            elif state.get("adjective_grammar"):
                grammar_obj = state["adjective_grammar"] 
                word_type = "adjective"
            elif state.get("verb_grammar"):
                grammar_obj = state["verb_grammar"]
                word_type = "verb"
            
            if grammar_obj and word_type:
                # Generate flashcards
                flashcards = flashcard_generator.generate_flashcards_from_grammar(grammar_obj, word_type)
                
                # Save flashcards to database
                saved_count = flashcard_generator.save_flashcards_to_database(flashcards)
                
                message = f"Generated and saved {saved_count}/{len(flashcards)} flashcards for '{grammar_obj.dictionary_form}'"
                
                return {
                    **state,
                    "flashcards_generated": saved_count,
                    "flashcard_generation_message": message
                }
            else:
                return {
                    **state,
                    "flashcards_generated": 0,
                    "flashcard_generation_message": "No grammar data available for flashcard generation"
                }
                
        except Exception as e:
            error_message = f"Error generating flashcards: {str(e)}"
            if writer and hasattr(writer, 'write'):
                writer.write(f"{error_message}\n")
                
            return {
                **state,
                "flashcards_generated": 0,
                "flashcard_generation_message": error_message
            }

    def _build_graph(self) -> RunnableSerializable:
        """Build the LangGraph for the Russian language tutor"""

        workflow = StateGraph(State)

        # Define the nodes
        workflow.add_node("initial_classification", self.initial_classification)
        workflow.add_node("get_noun_grammar", self.get_noun_grammar)
        workflow.add_node("get_adjective_grammar", self.get_adjective_grammar)
        workflow.add_node("get_verb_grammar", self.get_verb_grammar)
        workflow.add_node("flashcard_generation", self.generate_flashcards)

        # Define the edges
        workflow.add_edge(START, "initial_classification")

        # Route based on word type
        workflow.add_conditional_edges(
            "initial_classification",
            lambda state: state.get("classification").word_type if state.get("classification") else "noun",
            {
                "noun": "get_noun_grammar",
                "adjective": "get_adjective_grammar",
                "verb": "get_verb_grammar",
                # Add more word types and handlers here as you implement them
                # Default to end for any word type without a specific handler
                "__default__": END
            }
        )

        # Route from grammar nodes to either flashcard generation or END
        def should_generate_flashcards(state):
            return "flashcard_generation" if state.get("generate_flashcards") else "__end__"
        
        # Connect grammar nodes to conditional flashcard generation
        workflow.add_conditional_edges("get_noun_grammar", should_generate_flashcards)
        workflow.add_conditional_edges("get_adjective_grammar", should_generate_flashcards)
        workflow.add_conditional_edges("get_verb_grammar", should_generate_flashcards)
        
        # Connect flashcard generation to END
        workflow.add_edge("flashcard_generation", END)

        return workflow.compile()

    def invoke(
            self,
            input_text: str,
            generate_flashcards: bool = False,
            config: Optional[RunnableConfig] = None
    ) -> Dict:
        """Run the language tutor graph with the given input"""

        # Initialize the state with the user's input
        initial_state = {
            "original_human_input": input_text,
            "classification": None,
            "noun_grammar": None,
            "adjective_grammar": None,
            "verb_grammar": None,
            "final_answer": None,
            "generate_flashcards": generate_flashcards,
            "flashcards_generated": None,
            "flashcard_generation_message": None
        }

        # Execute the graph
        result = self.graph.invoke(initial_state, config=config)

        return result

