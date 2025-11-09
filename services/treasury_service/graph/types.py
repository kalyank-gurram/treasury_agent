"""Common types for the Treasury Agent graph."""

from typing import TypedDict, Any

class AgentState(TypedDict, total=False):
    question: str
    intent: str
    entity: str
    result: Any
    notes: str