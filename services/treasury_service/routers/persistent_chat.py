"""
Enhanced chat router with memory support.

Extends the existing chat router to support conversation persistence,
session management, and stateful interactions.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from ..schemas.chat import ChatIn, ChatOut
from ..services.persistent_chat import PersistentChatService, create_persistent_chat_service
from ..domain.entities.user import User
from ..infrastructure.security.auth_middleware import AuthMiddleware
from ..infrastructure.observability import get_observability_manager
from ..domain.services.treasury_services import TreasuryDomainService


router = APIRouter(tags=["Persistent Chat"])

# Constants
LOGGER_NAME = "api.persistent_chat"


# Enhanced schemas for memory-aware chat
class ChatStartRequest(BaseModel):
    """Request to start new conversation or resume session."""
    session_id: Optional[str] = None
    entities: List[str] = []


class ChatStartResponse(BaseModel):
    """Response when starting conversation."""
    session_id: str
    user_id: str
    role: str
    entities: List[str] 
    conversation_count: int
    message: str


class MemoryChatRequest(BaseModel):
    """Chat request with memory context."""
    message: str
    session_id: str
    thread_id: Optional[str] = None


class MemoryChatResponse(BaseModel):
    """Chat response with memory context."""
    id: str
    role: str
    content: str
    timestamp: str
    session_id: str
    thread_id: str
    conversation_count: int
    intent: str


class ConversationHistoryResponse(BaseModel):
    """User's conversation history."""
    conversations: List[Dict[str, Any]]
    total_count: int


# Dependency functions
def get_persistent_chat_service(request: Request) -> PersistentChatService:
    """Get persistent chat service with DI container."""
    container = request.app.state.container
    treasury_service = container.get(TreasuryDomainService)
    return create_persistent_chat_service(treasury_service, container)


def get_auth_middleware(request: Request) -> AuthMiddleware:
    """Get auth middleware from DI container."""
    container = request.app.state.container
    return container.get(AuthMiddleware)


async def get_current_user(request: Request) -> User:
    """Dependency to get current authenticated user."""
    auth_middleware = get_auth_middleware(request)
    require_auth_dependency = auth_middleware.require_auth()
    return await require_auth_dependency(request)


# Memory-aware endpoints
@router.post("/start", response_model=ChatStartResponse)
async def start_conversation(
    start_req: ChatStartRequest,
    request: Request,
    chat_service: PersistentChatService = Depends(get_persistent_chat_service),
    current_user: User = Depends(get_current_user)
):
    """Start new conversation or resume existing session."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info(
        "Starting conversation",
        username=current_user.username,
        requested_session_id=start_req.session_id,
        entities=start_req.entities
    )
    
    try:
        # Use user's accessible entities if none specified
        entities = start_req.entities or current_user.entity_access
        
        context = await chat_service.start_conversation(
            user_id=current_user.username,
            role=current_user.role,
            entities=entities,
            session_id=start_req.session_id
        )
        
        logger.info(
            "Conversation started successfully",
            session_id=context.session_id,
            username=current_user.username
        )
        
        return ChatStartResponse(
            session_id=context.session_id,
            user_id=context.user_id,
            role=context.role,
            entities=context.entities,
            conversation_count=context.conversation_count,
            message=f"Conversation started. Session ID: {context.session_id}"
        )
        
    except Exception as e:
        logger.error(
            "Failed to start conversation",
            username=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.post("/memory/message", response_model=MemoryChatResponse)
async def send_memory_message(
    memory_req: MemoryChatRequest,
    request: Request,
    chat_service: PersistentChatService = Depends(get_persistent_chat_service),
    current_user: User = Depends(get_current_user)
):
    """Send chat message with conversation memory."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info(
        "Processing memory-aware chat message",
        username=current_user.username,
        session_id=memory_req.session_id,
        message_length=len(memory_req.message)
    )
    
    try:
        # Get conversation context
        memory_store = chat_service.memory_store
        context = memory_store._load_context(memory_req.session_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Session {memory_req.session_id} not found. Please start a new conversation."
            )
        
        # Verify user owns this session
        if context.user_id != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this conversation session."
            )
        
        # Process with memory
        result = await chat_service.process_chat_with_memory(
            question=memory_req.message,
            context=context,
            thread_id=memory_req.thread_id
        )
        
        response = MemoryChatResponse(
            id=f"msg_{int(datetime.now().timestamp() * 1000)}",
            role="assistant",
            content=result["formatted_response"],
            timestamp=datetime.now().isoformat(),
            session_id=result["session_id"],
            thread_id=result["thread_id"],
            conversation_count=result["conversation_count"],
            intent=result["intent"]
        )
        
        logger.info(
            "Memory chat message processed successfully",
            username=current_user.username,
            session_id=memory_req.session_id,
            intent=result["intent"]
        )
        
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(
            "Memory chat message processing failed",
            username=current_user.username,
            session_id=memory_req.session_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    request: Request,
    chat_service: PersistentChatService = Depends(get_persistent_chat_service),
    current_user: User = Depends(get_current_user)
):
    """Get user's conversation history."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info("Fetching conversation history", username=current_user.username)
    
    try:
        conversations = await chat_service.get_conversation_history(current_user.username)
        
        return ConversationHistoryResponse(
            conversations=conversations,
            total_count=len(conversations)
        )
        
    except Exception as e:
        logger.error(
            "Failed to fetch conversation history",
            username=current_user.username,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )


@router.post("/end/{session_id}")
async def end_conversation(
    session_id: str,
    request: Request,
    chat_service: PersistentChatService = Depends(get_persistent_chat_service),
    current_user: User = Depends(get_current_user)
):
    """End conversation and create summary."""
    observability = get_observability_manager()
    logger = observability.get_logger(LOGGER_NAME)
    
    logger.info(
        "Ending conversation",
        username=current_user.username,
        session_id=session_id
    )
    
    try:
        # Verify user owns this session
        memory_store = chat_service.memory_store
        context = memory_store._load_context(session_id)
        
        if context and context.user_id != current_user.username:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this conversation session."
            )
        
        summary = await chat_service.end_conversation(session_id)
        
        if summary:
            return {
                "message": "Conversation ended successfully",
                "summary": summary
            }
        else:
            return {"message": "Conversation not found or already ended"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to end conversation",
            username=current_user.username,
            session_id=session_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end conversation: {str(e)}"
        )