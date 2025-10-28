"""Logger node - Log execution trace"""

import logging
import json
from typing import Dict, Any


logger = logging.getLogger(__name__)


def log_trace(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log execution trace

    Args:
        state: Complete LangGraph state

    Returns:
        Unmodified state
    """
    trace_id = state.get("trace_id", "unknown")

    # Build log entry
    log_entry = {
        "trace_id": trace_id,
        "triage": state.get("triage", "unknown"),
        "red_flags": state.get("red_flag_check", {}).red_flags if state.get("red_flag_check") else [],
        "retrieved_docs_count": len(state.get("retrieved_docs", [])),
        "citations_count": len(state.get("citations", [])),
        "answer_length": len(state.get("answer", ""))
    }

    # Log features
    features = state.get("features")
    if features:
        log_entry["features"] = {
            "age": features.age,
            "symptoms": features.symptoms_list,
            "query_terms": features.query_terms
        }

    logger.info(f"Trace: {json.dumps(log_entry, indent=2)}")

    return state
