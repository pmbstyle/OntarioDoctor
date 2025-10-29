import json
import logging
from pathlib import Path
from typing import Dict, Any

from backend.shared.models import RedFlagCheck


logger = logging.getLogger(__name__)


# Load red-flag rules
RULES_PATH = Path(__file__).parent.parent / "rules.json"
with open(RULES_PATH) as f:
    RULES_DATA = json.load(f)
ER_RULES = RULES_DATA["er_rules"]


def check_red_flags(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for red-flag symptoms requiring immediate attention

    Args:
        state: LangGraph state with features and messages

    Returns:
        Updated state with red_flag_check
    """
    # Get features and user text
    features = state.get("features")
    messages = state.get("messages", [])

    user_text = ""
    for msg in reversed(messages):
        if msg.role == "user":
            user_text = msg.content.lower()
            break

    if not user_text:
        logger.warning("No user message found for red-flag check")
        state["red_flag_check"] = RedFlagCheck(er_required=False, red_flags=[])
        return state

    # Also check symptoms from features
    symptoms_from_features = []
    if features and hasattr(features, "symptoms_list"):
        symptoms_from_features = features.symptoms_list

    # Combine text and extracted symptoms
    all_text = user_text + " " + " ".join(symptoms_from_features)

    # Check against rules
    matched_rules = []
    for rule in ER_RULES:
        rule_symptoms = rule["symptoms"]

        # Check if ALL symptoms in rule are present
        all_present = all(symptom.lower() in all_text for symptom in rule_symptoms)

        if all_present:
            matched_rules.append(rule)
            logger.warning(f"Red flag detected: {rule['message']}")

    # Check for infant fever (special case)
    if features:
        age = features.age if hasattr(features, "age") else None
        fever = features.fever_c if hasattr(features, "fever_c") else None

        if age is not None and age == 0 and fever:
            # Infant with fever
            matched_rules.append({
                "symptoms": ["infant", "fever"],
                "action": "ER",
                "message": "Fever in infant under 3 months requires immediate ER evaluation"
            })

    # Create red flag check result
    er_required = len(matched_rules) > 0
    red_flags = [rule["message"] for rule in matched_rules]

    red_flag_check = RedFlagCheck(
        er_required=er_required,
        red_flags=red_flags,
        er_message=matched_rules[0]["message"] if matched_rules else None
    )

    logger.info(f"Red-flag check: ER required={er_required}, flags={len(red_flags)}")

    state["red_flag_check"] = red_flag_check

    # Set triage level
    if er_required:
        if any("911" in rule.get("action", "") for rule in matched_rules):
            state["triage"] = "911"
        else:
            state["triage"] = "ER"
    else:
        state["triage"] = "primary-care"

    return state
