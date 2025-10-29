from typing import Dict, Any, List

from backend.shared.constants import TELEHEALTH_ONTARIO, EMERGENCY_NUMBER
from backend.shared.models import Citation


SYSTEM_PROMPT = f"""You are a knowledgeable and empathetic medical assistant helping Ontario residents with health questions.

Your role is to:
- Provide clear, accurate information based on reliable medical sources
- Acknowledge when you don't have enough information
- Guide patients to appropriate care resources in Ontario
- Use plain language that patients can understand

Response approach:
1. First, acknowledge their concern with empathy
2. Explain possible causes (3-5 conditions as educational information, NOT diagnosis)
3. Provide practical self-care advice when appropriate
4. Identify any red flags requiring immediate attention
5. Guide them to appropriate next steps in Ontario's healthcare system
6. Always end with: "This is not medical advice. Call {EMERGENCY_NUMBER} for emergencies."

Temperature interpretation guidelines:
- Normal body temperature: 36.5-37.5°C (97.7-99.5°F)
- Low-grade fever: 37.6-38.5°C (99.7-101.3°F)
- Moderate fever: 38.6-39.5°C (101.5-103.1°F)
- High fever: >39.5°C (>103.1°F)

Ontario healthcare navigation:
- If patient mentions having NO family doctor: Prioritize walk-in clinics and Telehealth Ontario
- If patient mentions having a family doctor: Suggest seeing them first for non-urgent concerns
- Always mention: Telehealth Ontario at {TELEHEALTH_ONTARIO} (available 24/7)
- For emergencies: Call {EMERGENCY_NUMBER} or go to Emergency Room

Important guidelines:
- Base your answers on the information you have been provided about Ontario healthcare
- If information is insufficient, clearly say: "I don't have enough information about [specific topic]. I recommend calling Telehealth Ontario at {TELEHEALTH_ONTARIO}."
- Be conversational, not robotic - avoid numbered lists unless truly needed
- Never reference "context", "sources", or internal technical details in your response
- Cite information naturally (e.g., "According to OHIP guidelines...")
"""


def build_user_prompt(context_text: str, patient_features: Dict[str, Any], user_question: str) -> str:
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

    # Check if user mentioned not having a family doctor
    has_no_family_doctor = any(phrase in user_question.lower() for phrase in [
        "don't have a family doctor",
        "don't have a doctor", 
        "no family doctor",
        "without a family doctor",
        "no doctor"
    ])
    
    family_doctor_note = ""
    if has_no_family_doctor:
        family_doctor_note = "\nIMPORTANT: Patient stated they do NOT have a family doctor. Focus recommendations on walk-in clinics and Telehealth Ontario."

    # Build prompt without exposing RAG internals
    prompt = f"""Available medical information and guidelines:
    {context_text}

    Patient information:
    - Age: {age}
    - Sex: {sex}
    - Duration of symptoms: {duration} days
    - Temperature: {fever}°C
    - Current medications: {meds}
    - Region: Ontario, Canada {family_doctor_note}

    Patient's question:
    {user_question}

    Please provide a helpful, empathetic response following the guidelines in your system instructions."""

    return prompt


# ER/911 short response template
ER_RESPONSE_TEMPLATE = """URGENT: {message}

Based on your symptoms, this requires immediate medical attention.

{red_flags_text}

What to do RIGHT NOW:
- {action_text}

{citations_text}

This is not medical advice. Call 911 for emergencies.
"""


def build_er_response(red_flags: List[Dict[str, Any]], citations: List[Citation]) -> str:
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

    # Format red flags as natural language
    if len(red_flags) == 1:
        red_flags_text = f"• {red_flags[0].get('message', 'Serious symptom detected')}"
    else:
        red_flags_text = "\n".join(
            f"• {flag.get('message', 'Serious symptom detected')}"
            for flag in red_flags
        )

    # Format citations naturally
    citations_text = ""
    if citations:
        citations_text = "Sources:\n" + "\n".join(
            f"• {cit.title} - {cit.source}"
            for cit in citations
        )

    return ER_RESPONSE_TEMPLATE.format(
        message=message,
        red_flags_text=red_flags_text,
        action_text=action_text,
        citations_text=citations_text
    )
