"""System prompts for Ontario-specific medical assistant"""

from backend.shared.constants import TELEHEALTH_ONTARIO, EMERGENCY_NUMBER


SYSTEM_PROMPT = f"""You are a Canadian medical assistant for Ontario residents.

Use ONLY the provided CONTEXT to answer. Do not use external knowledge.

Output structure:
1) Possible causes (3–5 conditions; NOT a diagnosis, just possibilities based on the information)
2) Red flags (if any serious symptoms are present that require immediate attention)
3) What to do next in Ontario:
   - For non-urgent concerns: See your family doctor or visit a walk-in clinic
   - For medical questions: Call Telehealth Ontario at {TELEHEALTH_ONTARIO} (available 24/7)
   - For emergencies: Call {EMERGENCY_NUMBER} or go to the Emergency Room
4) Numbered citations [1]..[N] matching the CONTEXT sources

IMPORTANT:
- Base your answer ONLY on the provided CONTEXT
- If CONTEXT doesn't contain enough information, say so
- Always mention Ontario-specific resources (family doctor, walk-in clinic, Telehealth Ontario)
- Always append: "This is not medical advice. Call {EMERGENCY_NUMBER} for emergencies."
- Be concise, clear, and avoid speculation beyond the sources
"""


def build_user_prompt(context_text: str, patient_features: dict, user_question: str) -> str:
    """
    Build user prompt with context, patient info, and question

    Args:
        context_text: Formatted context with citations [1], [2], etc.
        patient_features: Dictionary with age, sex, symptoms, etc.
        user_question: User's original question

    Returns:
        Formatted user prompt
    """
    # Extract patient features
    age = patient_features.get("age", "unknown")
    sex = patient_features.get("sex", "unknown")
    duration = patient_features.get("duration_days", "unknown")
    fever = patient_features.get("fever_c", "none")
    meds = ", ".join(patient_features.get("meds", [])) or "none"

    prompt = f"""CONTEXT:
{context_text}

PATIENT:
age={age}, sex={sex}, duration_days={duration}, fever_c={fever}, meds={meds}, region=CA-ON

QUESTION:
{user_question}
"""

    return prompt


# ER/911 short response template
ER_RESPONSE_TEMPLATE = """⚠️ URGENT: {message}

Based on your symptoms, this requires immediate medical attention.

{red_flags_text}

What to do RIGHT NOW:
- {action_text}

{citations_text}

This is not medical advice. Call 911 for emergencies.
"""


def build_er_response(red_flags: list, citations: list) -> str:
    """
    Build emergency response with red flags

    Args:
        red_flags: List of red flag dictionaries
        citations: List of Citation objects

    Returns:
        Formatted emergency response
    """
    if not red_flags:
        return ""

    # Get the first (most serious) red flag
    primary_flag = red_flags[0]
    message = primary_flag.get("message", "Immediate medical attention required")
    action = primary_flag.get("action", "ER")

    # Format action text
    if action == "911":
        action_text = f"Call {EMERGENCY_NUMBER} immediately"
    elif action == "ER":
        action_text = f"Go to the Emergency Room immediately or call {EMERGENCY_NUMBER}"
    else:
        action_text = "Seek immediate medical attention"

    # Format red flags
    red_flags_text = "Red flags detected:\n"
    for i, flag in enumerate(red_flags, 1):
        red_flags_text += f"{i}. {flag.get('message', 'Serious symptom detected')}\n"

    # Format citations
    citations_text = ""
    if citations:
        citations_text = "Sources:\n"
        for cit in citations:
            citations_text += f"[{cit.id}] {cit.title} - {cit.source}\n"

    return ER_RESPONSE_TEMPLATE.format(
        message=message,
        red_flags_text=red_flags_text,
        action_text=action_text,
        citations_text=citations_text
    )
