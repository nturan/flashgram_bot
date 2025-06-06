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

class State(TypedDict):
    original_human_input: str
    classification: Optional[WordClassification]
    noun_grammar: Optional[Noun]
    adjective_grammar: Optional[Adjective]
    verb_grammar: Optional[Verb]
    final_answer: Optional[str]


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

    def _build_graph(self) -> RunnableSerializable:
        """Build the LangGraph for the Russian language tutor"""

        workflow = StateGraph(State)

        # Define the nodes
        workflow.add_node("initial_classification", self.initial_classification)
        workflow.add_node("get_noun_grammar", self.get_noun_grammar)
        workflow.add_node("get_adjective_grammar", self.get_adjective_grammar)
        workflow.add_node("get_verb_grammar", self.get_verb_grammar)

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

        # Connect noun grammar to END
        workflow.add_edge("get_noun_grammar", END)

        # Connect adjective grammar to END
        workflow.add_edge("get_adjective_grammar", END)

        # Connect verb grammar to END
        workflow.add_edge("get_verb_grammar", END)

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
            "verb_grammar": None,
            "final_answer": None
        }

        # Execute the graph
        result = self.graph.invoke(initial_state, config=config)

        return result

