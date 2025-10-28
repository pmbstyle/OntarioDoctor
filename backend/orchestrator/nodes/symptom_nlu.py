"""Symptom NLU node - Extract features from user message"""

import re
import logging
from typing import Dict, Any

from backend.shared.models import PatientFeatures


logger = logging.getLogger(__name__)


def extract_features(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract patient features from messages

    Args:
        state: LangGraph state with messages

    Returns:
        Updated state with features
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    # Get last user message
    user_message = None
    for msg in reversed(messages):
        if msg.role == "user":
            user_message = msg.content
            break

    if not user_message:
        return state

    text = user_message.lower()

    # Extract age
    age = None
    age_patterns = [
        r"(\d+)\s*(?:year|yr|y\.o\.|years old)",
        r"age\s*(\d+)",
        r"(\d+)\s*(?:month|mo|months old)"  # Convert months to years
    ]
    for pattern in age_patterns:
        match = re.search(pattern, text)
        if match:
            age = int(match.group(1))
            if "month" in pattern:
                age = 0  # Infants
            break

    # Extract sex
    sex = None
    if re.search(r"\b(male|man|boy|son|father|husband|he|him|his)\b", text):
        sex = "M"
    elif re.search(r"\b(female|woman|girl|daughter|mother|wife|she|her)\b", text):
        sex = "F"

    # Extract duration
    duration_days = None
    duration_patterns = [
        (r"(\d+)\s*day", 1),
        (r"(\d+)\s*week", 7),
        (r"(\d+)\s*month", 30),
        (r"(\d+)\s*hour", 1),  # Round up to 1 day
    ]
    for pattern, multiplier in duration_patterns:
        match = re.search(pattern, text)
        if match:
            duration_days = int(match.group(1)) * multiplier
            break

    # Extract fever
    fever_c = None
    # Check for Celsius
    celsius_match = re.search(r"(\d+\.?\d*)\s*[°]?c", text)
    if celsius_match:
        fever_c = float(celsius_match.group(1))
    else:
        # Check for Fahrenheit and convert
        fahrenheit_match = re.search(r"(\d+\.?\d*)\s*[°]?f", text)
        if fahrenheit_match:
            temp_f = float(fahrenheit_match.group(1))
            fever_c = (temp_f - 32) * 5 / 9

    # Extract symptoms (simple keyword matching)
    symptom_keywords = [
        "fever", "cough", "sore throat", "headache", "nausea", "vomiting",
        "diarrhea", "chest pain", "shortness of breath", "difficulty breathing",
        "rash", "fatigue", "weakness", "dizziness", "confusion",
        "stiff neck", "abdominal pain", "ear pain", "runny nose",
        "congestion", "chills", "sweating", "muscle aches", "joint pain"
    ]
    symptoms_list = [kw for kw in symptom_keywords if kw in text]

    # Extract medications
    med_keywords = [
        "tylenol", "acetaminophen", "paracetamol",
        "advil", "ibuprofen", "motrin",
        "aspirin",
        "antibiotics", "amoxicillin", "penicillin",
        "antihistamine", "benadryl",
        "cough syrup", "cough medicine"
    ]
    meds = [med for med in med_keywords if med in text]

    # Generate query terms (for retrieval)
    query_terms = symptoms_list.copy()
    if age is not None:
        if age == 0:
            query_terms.append("infant")
        elif age < 12:
            query_terms.append("child")
        else:
            query_terms.append("adult")
    if duration_days:
        if duration_days <= 2:
            query_terms.append("acute")
        else:
            query_terms.append("persistent")

    # Create features
    features = PatientFeatures(
        age=age,
        sex=sex,
        duration_days=duration_days,
        fever_c=fever_c,
        symptoms_list=symptoms_list,
        meds=meds,
        query_terms=query_terms if query_terms else symptoms_list
    )

    logger.info(f"Extracted features: {features}")

    # Update state
    state["features"] = features
    return state
