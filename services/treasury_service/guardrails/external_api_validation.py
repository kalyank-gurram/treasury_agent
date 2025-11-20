"""External API-based validation for factuality and hallucination prevention."""
from typing import Dict, Any

def validate_with_api(response: str, api_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if response matches or is supported by external API result.
    Returns safe=False if response is not validated by API.
    """
    # Example: Assume api_result contains a 'valid' boolean and 'reason'
    if api_result.get("valid", False):
        return {"safe": True}
    return {"safe": False, "reason": api_result.get("reason", "Response not validated by external API.")}
