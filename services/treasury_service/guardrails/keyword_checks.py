"""Keyword-based guardrails for input/output validation."""
import re
from typing import Dict, Any

FORBIDDEN_KEYWORDS = [
    "password", "ssn", "social security", "credit card", "offensive", "hate", "violence",
    "drop table", "delete from", "insert into", "select *", "--", ";", "/*", "*/", "xp_", "exec", "union select", "or 1=1", "prompt injection", "ignore previous", "system:"
]
PROFANITY = ["damn", "hell", "shit", "fuck", "bitch", "bastard"]
ALL_FORBIDDEN = FORBIDDEN_KEYWORDS + PROFANITY
FORBIDDEN_REGEX = re.compile(r"(" + "|".join(re.escape(k) for k in ALL_FORBIDDEN) + ")", re.IGNORECASE)

MAX_QUERY_LENGTH = 512

def validate_input(query: str) -> Dict[str, Any]:
    if not query or not query.strip():
        return {"valid": False, "reason": "Query is empty."}
    if len(query) > MAX_QUERY_LENGTH:
        return {"valid": False, "reason": f"Query exceeds max length ({MAX_QUERY_LENGTH})."}
    if FORBIDDEN_REGEX.search(query):
        return {"valid": False, "reason": "Query contains forbidden, unsafe, or profane content."}
    if re.search(r"('|\"|;|--|/\*|\*/|xp_|exec|union select|or 1=1)", query, re.IGNORECASE):
        return {"valid": False, "reason": "Query contains possible SQL injection or prompt injection."}
    return {"valid": True}

def filter_output(response: str) -> Dict[str, Any]:
    if FORBIDDEN_REGEX.search(response):
        return {"safe": False, "reason": "Response contains forbidden, unsafe, or profane content."}
    if re.search(r"('|\"|;|--|/\*|\*/|xp_|exec|union select|or 1=1)", response, re.IGNORECASE):
        return {"safe": False, "reason": "Response contains possible SQL injection or prompt injection."}
    return {"safe": True}
