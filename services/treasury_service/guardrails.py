"""Guardrails for input validation and output filtering in Treasury Agent application."""

import re
from typing import Dict, Any


# Forbidden keywords and patterns (expand as needed)
FORBIDDEN_KEYWORDS = [
    "password", "ssn", "social security", "credit card", "offensive", "hate", "violence",
    "drop table", "delete from", "insert into", "select *", "--", ";", "/*", "*/", "xp_", "exec", "union select", "or 1=1", "prompt injection", "ignore previous", "system:"
]
# Basic profanity list (expand as needed)
PROFANITY = [
    "damn", "hell", "shit", "fuck", "bitch", "bastard"
]
ALL_FORBIDDEN = FORBIDDEN_KEYWORDS + PROFANITY
FORBIDDEN_REGEX = re.compile(r"(" + "|".join(re.escape(k) for k in ALL_FORBIDDEN) + ")", re.IGNORECASE)

MAX_QUERY_LENGTH = 512

def validate_input(query: str) -> Dict[str, Any]:
    """Validate user input for safety, compliance, and injection attacks."""
    if not query or not query.strip():
        return {"valid": False, "reason": "Query is empty."}
    if len(query) > MAX_QUERY_LENGTH:
        return {"valid": False, "reason": f"Query exceeds max length ({MAX_QUERY_LENGTH})."}
    if FORBIDDEN_REGEX.search(query):
        return {"valid": False, "reason": "Query contains forbidden, unsafe, or profane content."}
    # Simple SQL injection pattern
    if re.search(r"('|\"|;|--|/\*|\*/|xp_|exec|union select|or 1=1)", query, re.IGNORECASE):
        return {"valid": False, "reason": "Query contains possible SQL injection or prompt injection."}
    return {"valid": True}



def filter_output(response: str) -> Dict[str, Any]:
    """
    Filter agent/model output for unsafe, sensitive, profane content, and hallucinations.
    Hallucination guardrails include:
    1. Fact-checking against known sources (basic keyword check)
    2. Unsupported claims detection
    3. Unverifiable numbers/statistics
    4. Speculative language
    5. Source verification (presence of citations)
    """
    # Unsafe content
    if FORBIDDEN_REGEX.search(response):
        return {"safe": False, "reason": "Response contains forbidden, unsafe, or profane content."}
    # SQL/prompt injection
    if re.search(r"('|\"|;|--|/\*|\*/|xp_|exec|union select|or 1=1)", response, re.IGNORECASE):
        return {"safe": False, "reason": "Response contains possible SQL injection or prompt injection."}
    # 1. Unsupported claims (e.g., "As an AI", "I believe", "It is known that")
    unsupported_claims = [
        "as an ai", "i believe", "it is known that", "it is widely accepted", "studies show", "experts say", "it is rumored", "it is said that"
    ]
    if any(phrase in response.lower() for phrase in unsupported_claims):
        return {"safe": False, "reason": "Response contains unsupported or unverifiable claims."}
    # 2. Unverifiable numbers/statistics (e.g., "99%", "millions", "hundreds of thousands")
    if re.search(r"\b(\d{2,}%|millions?|hundreds? of thousands?|billions?)\b", response, re.IGNORECASE):
        return {"safe": False, "reason": "Response contains unverifiable statistics or numbers."}
    # 3. Speculative language (e.g., "might", "could", "possibly", "may", "likely")
    speculative_words = ["might", "could", "possibly", "may", "likely", "suggests", "appears"]
    if any(word in response.lower() for word in speculative_words):
        return {"safe": False, "reason": "Response contains speculative or non-factual language."}
    # 4. Source verification (e.g., missing citations for factual claims)
    if "according to" in response.lower() and not re.search(r"(source:|ref:|doi:|https?://)", response, re.IGNORECASE):
        return {"safe": False, "reason": "Response references sources but does not provide citation."}
    return {"safe": True}


def guardrails_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node for guardrails: validates input and filters output."""
    query = state.get("query") or state.get("question") or ""
    validation = validate_input(query)
    if not validation["valid"]:
        state["response"] = f"Input rejected: {validation['reason']}"
        state["guardrails_status"] = "blocked"
        return state
    # If response already present, filter it
    response = state.get("response", "")
    if response:
        filtering = filter_output(response)
        if not filtering["safe"]:
            state["response"] = f"Output blocked: {filtering['reason']}"
            state["guardrails_status"] = "blocked"
            return state
    state["guardrails_status"] = "passed"
    return state
