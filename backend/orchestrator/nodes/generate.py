"""Generate node - Call vLLM (Text Generation Inference) for answer generation"""

import logging
import httpx
from typing import Dict, Any

from backend.orchestrator.prompts import SYSTEM_PROMPT, build_user_prompt, build_er_response
from backend.shared.constants import LLM_TEMPERATURE, LLM_MAX_TOKENS


logger = logging.getLogger(__name__)


async def generate_answer(state: Dict[str, Any], vllm_url: str = "http://localhost:80") -> Dict[str, Any]:
    """
    Generate answer using vLLM (Text Generation Inference)

    Args:
        state: LangGraph state with context_text, features, messages
        vllm_url: vLLM service URL

    Returns:
        Updated state with answer
    """
    # Check if ER path (skip LLM, use template)
    red_flag_check = state.get("red_flag_check")
    if red_flag_check and red_flag_check.er_required:
        logger.info("ER path detected, using template response")

        # Build ER response
        er_response = build_er_response(
            red_flags=[{"message": msg} for msg in red_flag_check.red_flags],
            citations=state.get("citations", [])
        )
        state["answer"] = er_response
        return state

    # Standard path: call vLLM
    context_text = state.get("context_text", "")
    features = state.get("features")
    messages = state.get("messages", [])

    # Get user question
    user_question = ""
    for msg in reversed(messages):
        if msg.role == "user":
            user_question = msg.content
            break

    if not context_text or not user_question:
        logger.error("Missing context or user question for generation")
        state["answer"] = "I don't have enough information to answer your question."
        return state

    # Build prompts
    patient_features_dict = {
        "age": features.age if features else None,
        "sex": features.sex if features else None,
        "duration_days": features.duration_days if features else None,
        "fever_c": features.fever_c if features else None,
        "meds": features.meds if features else []
    }

    user_prompt = build_user_prompt(context_text, patient_features_dict, user_question)

    # Format prompt manually (Meditron-7B is a base model without chat template)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}\n\nAnswer:"

    logger.info("Calling vLLM for answer generation...")

    # Call vLLM (OpenAI-compatible API) using completions endpoint
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{vllm_url}/v1/completions",
                json={
                    "model": "epfl-llm/meditron-7b",
                    "prompt": full_prompt,
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS,
                    "stop": ["\n\n", "Question:", "User:"],
                    "stream": False
                }
            )
            response.raise_for_status()

            result = response.json()
            answer = result["choices"][0]["text"].strip()

            logger.info(f"Generated answer ({len(answer)} chars)")
            state["answer"] = answer

    except Exception as e:
        logger.error(f"vLLM generation failed: {e}", exc_info=True)
        state["answer"] = (
            "I apologize, but I'm having trouble generating a response right now. "
            "Please call Telehealth Ontario at 1-866-797-0000 for medical advice."
        )

    return state
