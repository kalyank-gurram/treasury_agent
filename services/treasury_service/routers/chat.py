from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from ..schemas.chat import ChatIn, ChatOut
from ..services.chat import ChatService
from ..domain.entities.user import User, Permission
from ..infrastructure.security.auth_middleware import AuthMiddleware
from ..infrastructure.observability import (
    get_observability_manager,
    trace_operation,
    monitor_performance
)

router = APIRouter(tags=["Chat"])

# Constants
LOGGER_NAME = "api.chat"

# Additional schemas for the new endpoints
class ChatMessage(BaseModel):
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str

class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


def get_chat_service(request: Request) -> ChatService:
    """Get chat service with DI container."""
    container = request.app.state.container
    return container.get(ChatService)


def get_auth_middleware(request: Request) -> AuthMiddleware:
    """Get auth middleware from DI container."""
    container = request.app.state.container
    return container.get(AuthMiddleware)


async def get_current_user(request: Request) -> User:
    """Dependency to get current authenticated user."""
    auth_middleware = get_auth_middleware(request)
    require_auth_dependency = auth_middleware.require_auth()
    return await require_auth_dependency(request)


@router.get("/history", response_model=List[ChatMessage])
async def get_chat_history(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get chat history for the current user."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info("Fetching chat history", username=current_user.username)
    
    # For now, return empty history - in production, implement actual storage
    return []


@router.post("/message", response_model=ChatMessage)
async def send_message(
    message_req: MessageRequest,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message and get AI response."""
    observability = get_observability_manager()
    logger = observability.get_logger("api.chat")
    
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info(
        "Processing chat message",
        username=current_user.username,
        message_length=len(message_req.message)
    )
    
    try:
        # Process the chat message using the existing chat service
        result = await chat_service.process_chat(message_req.message, current_user.entity_access[0] if current_user.entity_access else None)
        
        # Format response as ChatMessage using the formatted response
        response = ChatMessage(
            id=str(hash(f"{current_user.username}_{datetime.now().isoformat()}")),
            role="assistant",
            content=result.get("formatted_response", result.get("result", "I'm sorry, I couldn't process that request.")),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("Chat message processed successfully", username=current_user.username)
        
        return response
        
    except Exception as e:
        logger.error(
            "Chat message processing failed",
            username=current_user.username,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Return error as assistant message
        return ChatMessage(
            id=str(hash(f"{current_user.username}_error_{datetime.now().isoformat()}")),
            role="assistant", 
            content="I'm sorry, I encountered an error processing your request. Please try again.",
            timestamp=datetime.now().isoformat()
        )


@router.post("", response_model=ChatOut)
async def chat(
    inp: ChatIn,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user)
):
    """Chat endpoint with observability and dependency injection."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    # Check entity access if entity is specified
    if inp.entity and not current_user.can_access_entity(inp.entity):
        logger.warning(
            "Entity access denied",
            username=current_user.username,
            entity=inp.entity,
            user_entities=current_user.entity_access
        )
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to entity: {inp.entity}"
        )
    
    # Log request
    logger.info(
        "Processing chat request",
        username=current_user.username,
        entity=inp.entity,
        question_length=len(inp.question) if inp.question else 0
    )
    
    try:
        # Process chat request
        result = await chat_service.process_chat(inp.question, inp.entity)
        
        # Log success
        logger.info(
            "Chat request processed successfully",
            intent=result.get("intent"),
            entity=inp.entity
        )
        
        # Record success metric
        observability.record_metric(
            "counter", "chat_requests_total", 1,
            {"status": "success", "intent": result.get("intent", "unknown")}
        )
        
        return ChatOut(**result)
        
    except Exception as e:
        # Log error
        logger.error(
            "Chat request failed",
            entity=inp.entity,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Record error metric
        observability.record_metric(
            "counter", "chat_requests_total", 1,
            {"status": "error", "error_type": type(e).__name__}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )