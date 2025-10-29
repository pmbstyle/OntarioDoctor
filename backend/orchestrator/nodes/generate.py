import logging
import httpx
from typing import Dict, Any

from backend.orchestrator.prompts import SYSTEM_PROMPT, build_user_prompt, build_er_response
from backend.shared.constants import LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_MODEL


logger = logging.getLogger(__name__)


async def generate_answer(state: Dict[str, Any], ollama_url: str = "http://localhost:11434") -> Dict[str, Any]:
    """
    Generate answer using Ollama (MedGemma-4B instruction-tuned model)

    Args:
        state: LangGraph state with context_text, features, messages
        ollama_url: Ollama service URL

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

    # Standard path: call Ollama
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

    logger.info("Calling Ollama (MedGemma-4B-IT) for answer generation...")

    # Call Ollama chat API (MedGemma-4B is instruction-tuned, supports chat format)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": LLM_TEMPERATURE,
                        "num_predict": LLM_MAX_TOKENS
                    }
                }
            )
            response.raise_for_status()

            result = response.json()
            answer = result["message"]["content"].strip()

            logger.info(f"Generated answer ({len(answer)} chars)")
            state["answer"] = answer

    except Exception as e:
        logger.error(f"Ollama generation failed: {e}", exc_info=True)
        state["answer"] = (
            "I apologize, but I'm having trouble generating a response right now. "
            "Please call Telehealth Ontario at 1-866-797-0000 for medical advice."
        )

    return state
