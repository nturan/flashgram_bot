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
)

class State(TypedDict):
    original_human_input: str
    classification: Optional[Dict]
    noun_grammar: Optional[str]
    adjective_grammar: Optional[str]
    final_answer: Optional[str]

# Define word types as a type alias instead of a class
WordType = Literal["noun", "verb", "adjective", "adverb", "preposition", "number"]

class RussianTutor:
    def __init__(self, api_key: SecretStr, model: str = "gpt-4o"):
        self.llm = ChatOpenAI(api_key=api_key, model=model)

        self.initial_classification_chain = (
            initial_classification_prompt
            | self.llm
            | StrOutputParser()
        )

        self.get_noun_grammar_chain: RunnableSerializable[dict[Any, Any], str] = (
            get_noun_grammar_prompt
            | self.llm
            | StrOutputParser()
        )

        self.get_adjective_grammar_chain: RunnableSerializable[dict[Any, Any], str] = (
            get_adjective_grammar_prompt
            | self.llm
            | StrOutputParser()
        )

        self.graph = self._build_graph()

    def initial_classification(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Classify the input word and determine its part of speech"""
        if writer and hasattr(writer, 'write'):
            writer.write("Analyzing input...\n")

        result = self.initial_classification_chain.invoke(
            {"word": state["original_human_input"]},
            config=config
        )

        # Parse the result to determine word type
        # This is a simplified version - in a real implementation you would
        # parse the LLM response more carefully
        word_type = "noun"  # Default to noun for this example
        russian_word = state["original_human_input"]

        if "noun" in result.lower():
            word_type = "noun"
        elif "verb" in result.lower():
            word_type = "verb"
        elif "adjective" in result.lower():
            word_type = "adjective"
        elif "adverb" in result.lower():
            word_type = "adverb"
        elif "preposition" in result.lower():
            word_type = "preposition"
        elif "number" in result.lower():
            word_type = "number"

        # Extract the Russian word if translation was performed
        for line in result.split("\n"):
            if "russian:" in line.lower():
                russian_word = line.split(":", 1)[1].strip()
                break

        return {
            **state,
            "classification": {
                "word_type": word_type,
                "russian_word": russian_word
            }
        }

    def get_noun_grammar(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Get grammar details for a Russian noun"""
        if writer and hasattr(writer, 'write'):
            writer.write("Getting noun grammar details...\n")

        word = state.get("classification", {}).get("russian_word", state["original_human_input"])

        result: str = self.get_noun_grammar_chain.invoke(
            {"word": word}, config=config
        )

        return {
            **state,
            "noun_grammar": result,
            "final_answer": result
        }

    def get_adjective_grammar(
            self, state: State, writer: Optional[StreamWriter] = None, config: Optional[RunnableConfig] = None,
    ) -> State:
        """Get grammar details for a Russian adjective"""
        if writer and hasattr(writer, 'write'):
            writer.write("Getting adjective grammar details...\n")

        word = state.get("classification", {}).get("russian_word", state["original_human_input"])

        result: str = self.get_adjective_grammar_chain.invoke(
            {"word": word}, config=config
        )

        return {
            **state,
            "adjective_grammar": result,
            "final_answer": result
        }

    def _build_graph(self) -> RunnableSerializable:
        """Build the LangGraph for the Russian language tutor"""

        workflow = StateGraph(State)

        # Define the nodes
        workflow.add_node("initial_classification", self.initial_classification)
        workflow.add_node("get_noun_grammar", self.get_noun_grammar)
        workflow.add_node("get_adjective_grammar", self.get_adjective_grammar)

        # Define the edges
        workflow.add_edge(START, "initial_classification")

        # Route based on word type
        workflow.add_conditional_edges(
            "initial_classification",
            lambda state: state.get("classification", {}).get("word_type", "noun"),
            {
                "noun": "get_noun_grammar",
                "adjective": "get_adjective_grammar",
                # Add more word types and handlers here as you implement them
                # "verb": "get_verb_grammar",
                # Default to end for any word type without a specific handler
                "__default__": END
            }
        )

        # Connect noun grammar to END
        workflow.add_edge("get_noun_grammar", END)

        # Connect adjective grammar to END
        workflow.add_edge("get_adjective_grammar", END)

        return workflow.compile()

    def invoke(
            self,
            input_text: str,
            config: Optional[RunnableConfig] = None
    ) -> Dict:
        """Run the language tutor graph with the given input"""

        # Initialize the state with the user's input
        initial_state = {
            "original_human_input": input_text,
            "classification": None,
            "noun_grammar": None,
            "adjective_grammar": None,
            "final_answer": None
        }

        # Execute the graph
        result = self.graph.invoke(initial_state, config=config)

        return result

