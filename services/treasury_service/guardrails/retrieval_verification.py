
"""Enterprise-grade retrieval-based verification for hallucination prevention."""

import logging
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Configure logging for auditability
logger = logging.getLogger("retrieval_verification")
logger.setLevel(logging.INFO)
# You may want to configure handlers in your main app

# Load embedding model (can be configured)
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

# Default similarity threshold (configurable)
SIMILARITY_THRESHOLD = 0.75

def verify_with_retrieval(response: str, retrieved_docs: List[str], threshold: float = SIMILARITY_THRESHOLD) -> Dict[str, Any]:
    """
    Verifies if the response is supported by retrieved documents using semantic similarity.
    Returns a detailed result for compliance and audit.
    """
    if not response or not retrieved_docs:
        logger.warning("Empty response or no retrieved documents provided.")
        return {"safe": False, "reason": "No response or retrieved documents to verify."}

    response_emb = model.encode(response, convert_to_tensor=True)
    docs_emb = model.encode(retrieved_docs, convert_to_tensor=True)
    similarities = util.cos_sim(response_emb, docs_emb)[0].cpu().numpy()

    max_sim = float(np.max(similarities))
    best_doc_idx = int(np.argmax(similarities))
    best_doc = retrieved_docs[best_doc_idx] if retrieved_docs else None

    result = {
        "safe": max_sim >= threshold,
        "similarity": max_sim,
        "best_doc": best_doc,
        "reason": "Response verified by retrieval." if max_sim >= threshold else "Response not sufficiently supported by retrieved documents.",
        "audit": {
            "similarities": similarities.tolist(),
            "threshold": threshold,
            "response": response,
            "retrieved_docs": retrieved_docs
        }
    }
    logger.info(f"Verification result: {result}")
    return result
