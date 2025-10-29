import logging
import uuid
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

from backend.shared.models import Message, Citation, PatientFeatures, RedFlagCheck
from backend.orchestrator.nodes.symptom_nlu import extract_features
from backend.orchestrator.nodes.guardrails import check_red_flags
from backend.orchestrator.nodes.retrieve import retrieve_documents
from backend.orchestrator.nodes.assemble import assemble_context
from backend.orchestrator.nodes.generate import generate_answer
from backend.orchestrator.nodes.logger import log_trace


logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """LangGraph state type"""
    messages: List[Message]
    features: PatientFeatures | None
    red_flag_check: RedFlagCheck | None
    retrieved_docs: List[dict]
    context_text: str | None 
    citations: List[Citation]
    answer: str | None
    triage: str
    trace_id: str


def create_graph(rag_url: str = "http://localhost:8001", ollama_url: str = "http://localhost:11434"):
    """
    Create LangGraph state machine

    Workflow:
    START → symptom_nlu → guardrails
                              ↓
                    [er_required?] ─Yes→ assemble → generate → logger → END
                              ↓ No
                          retrieve → assemble → generate → logger → END

    Args:
        rag_url: RAG service URL
        ollama_url: Ollama service URL

    Returns:
        Compiled graph
    """
    # Define async wrapper functions for nodes that need URL parameters
    async def retrieve_wrapper(state: GraphState) -> GraphState:
        return await retrieve_documents(state, rag_url)

    async def generate_wrapper(state: GraphState) -> GraphState:
        return await generate_answer(state, ollama_url)

    # Define graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("symptom_nlu", extract_features)
    workflow.add_node("guardrails", check_red_flags)
    workflow.add_node("retrieve", retrieve_wrapper)
    workflow.add_node("assemble", assemble_context)
    workflow.add_node("generate", generate_wrapper)
    workflow.add_node("logger", log_trace)

    # Define edges
    workflow.set_entry_point("symptom_nlu")

    workflow.add_edge("symptom_nlu", "guardrails")

    # Conditional edge after guardrails
    def should_retrieve(state: GraphState) -> str:
        """Decide whether to retrieve or go straight to generate"""
        red_flag_check = state.get("red_flag_check")
        if red_flag_check and red_flag_check.er_required:
            # ER path: skip retrieval, get minimal context
            logger.info("ER path: skipping retrieval")
            return "assemble"  # Will assemble from any available docs
        else:
            # Standard path: retrieve documents
            return "retrieve"

    workflow.add_conditional_edges(
        "guardrails",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "assemble": "assemble"
        }
    )

    workflow.add_edge("retrieve", "assemble")
    workflow.add_edge("assemble", "generate")
    workflow.add_edge("generate", "logger")
    workflow.add_edge("logger", END)

    # Compile graph
    graph = workflow.compile()

    logger.info("LangGraph compiled successfully")
    return graph


async def run_graph(messages: List[Message], rag_url: str, ollama_url: str) -> GraphState:
    """
    Run the graph with messages

    Args:
        messages: List of chat messages
        rag_url: RAG service URL
        ollama_url: Ollama service URL

    Returns:
        Final state
    """
    graph = create_graph(rag_url, ollama_url)

    # Initialize state
    initial_state = GraphState(
        messages=messages,
        features=None,
        red_flag_check=None,
        retrieved_docs=[],
        context_text=None,
        citations=[],
        answer=None,
        triage="primary-care",
        trace_id=str(uuid.uuid4())
    )

    # Run graph
    logger.info(f"Running graph with trace_id={initial_state['trace_id']}")
    final_state = await graph.ainvoke(initial_state)

    return final_state
