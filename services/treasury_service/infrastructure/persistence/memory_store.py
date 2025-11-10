"""
Memory and conversation persistence for Treasury Agent.

This module provides conversation memory, session management, and context persistence
for maintaining stateful interactions across requests.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from langgraph.checkpoint.memory import MemorySaver


@dataclass
class ConversationContext:
    """User conversation context and preferences."""
    user_id: str
    session_id: str
    entities: List[str]  # Accessible entities
    role: str  # CFO, manager, analyst
    preferences: Dict[str, Any]  # UI preferences, default filters
    created_at: datetime
    last_active: datetime
    conversation_count: int = 0


@dataclass
class ConversationSummary:
    """Summary of conversation for context retention."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    message_count: int
    key_topics: List[str]  # ["liquidity_analysis", "payment_approvals"] 
    entities_discussed: List[str]
    last_intent: str
    summary_text: str


class ConversationMemoryStore:
    """Manages conversation context, sessions, and memory persistence."""
    
    def __init__(self, db_path: str = "treasury_conversations.db"):
        self.db_path = Path(db_path)
        self._init_database()
        
        # LangGraph checkpointer for conversation state
        # Note: Using MemorySaver for now as SqliteSaver is not available in current LangGraph version
        # Our SQLite database handles persistent storage separately
        self.checkpointer = MemorySaver()
        
        # In-memory cache for active sessions
        self._active_contexts: Dict[str, ConversationContext] = {}
        self._session_timeout = timedelta(hours=24)  # 24-hour session timeout
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    user_id TEXT NOT NULL,
                    session_id TEXT PRIMARY KEY,
                    entities TEXT NOT NULL,  -- JSON array
                    role TEXT NOT NULL,
                    preferences TEXT NOT NULL,  -- JSON object
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    conversation_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER NOT NULL,
                    key_topics TEXT NOT NULL,  -- JSON array
                    entities_discussed TEXT NOT NULL,  -- JSON array
                    last_intent TEXT NOT NULL,
                    summary_text TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contexts_user_id ON conversation_contexts(user_id);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON conversation_summaries(user_id);
            """)
            
            conn.commit()
    
    def get_or_create_context(self, user_id: str, role: str, entities: List[str], 
                            session_id: Optional[str] = None) -> ConversationContext:
        """Get existing context or create new one."""
        # Check active sessions first
        active_session = self._find_active_session(user_id)
        if active_session:
            return active_session
        
        # Create new session if none specified
        if not session_id:
            session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            entities=entities,
            role=role,
            preferences={},
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        self._save_context(context)
        self._active_contexts[session_id] = context
        return context
    
    def update_context_activity(self, session_id: str):
        """Update last activity and conversation count."""
        if session_id in self._active_contexts:
            context = self._active_contexts[session_id]
            context.last_active = datetime.now()
            context.conversation_count += 1
            self._save_context(context)
        
        # Update in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE conversation_contexts 
                SET last_active = ?, conversation_count = conversation_count + 1
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            conn.commit()
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[ConversationSummary]:
        """Get recent conversation summaries for user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, user_id, start_time, end_time, message_count,
                       key_topics, entities_discussed, last_intent, summary_text
                FROM conversation_summaries
                WHERE user_id = ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (user_id, limit))
            
            summaries = []
            for row in cursor:
                summaries.append(ConversationSummary(
                    session_id=row[0],
                    user_id=row[1],
                    start_time=datetime.fromisoformat(row[2]),
                    end_time=datetime.fromisoformat(row[3]) if row[3] else None,
                    message_count=row[4],
                    key_topics=json.loads(row[5]),
                    entities_discussed=json.loads(row[6]),
                    last_intent=row[7],
                    summary_text=row[8]
                ))
            
            return summaries
    
    def create_conversation_summary(self, session_id: str, messages: List[Dict], 
                                  intents: List[str]) -> ConversationSummary:
        """Create summary for completed conversation."""
        context = self._active_contexts.get(session_id)
        if not context:
            # Load from database if not in cache
            context = self._load_context(session_id)
        
        if not context:
            raise ValueError(f"Context not found for session {session_id}")
        
        # Extract key information
        key_topics = list(set(intents))
        entities_discussed = context.entities
        
        # Generate summary text based on conversation
        summary_text = self._generate_summary_text(messages, intents, context)
        
        summary = ConversationSummary(
            session_id=session_id,
            user_id=context.user_id,
            start_time=context.created_at,
            end_time=datetime.now(),
            message_count=len(messages),
            key_topics=key_topics,
            entities_discussed=entities_discussed,
            last_intent=intents[-1] if intents else "unknown",
            summary_text=summary_text
        )
        
        self._save_summary(summary)
        return summary
    
    def get_checkpointer(self):
        """Get LangGraph checkpointer for conversation state."""
        return self.checkpointer
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory and mark in database."""
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, context in self._active_contexts.items():
            if current_time - context.last_active > self._session_timeout:
                expired_sessions.append(session_id)
        
        # Remove from active cache
        for session_id in expired_sessions:
            del self._active_contexts[session_id]
    
    def _find_active_session(self, user_id: str) -> Optional[ConversationContext]:
        """Find active session for user."""
        current_time = datetime.now()
        
        for context in self._active_contexts.values():
            if (context.user_id == user_id and 
                current_time - context.last_active < self._session_timeout):
                return context
        
        return None
    
    def _save_context(self, context: ConversationContext):
        """Save context to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_contexts
                (user_id, session_id, entities, role, preferences, 
                 created_at, last_active, conversation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context.user_id,
                context.session_id,
                json.dumps(context.entities),
                context.role,
                json.dumps(context.preferences),
                context.created_at.isoformat(),
                context.last_active.isoformat(),
                context.conversation_count
            ))
            conn.commit()
    
    def _load_context(self, session_id: str) -> Optional[ConversationContext]:
        """Load context from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_id, session_id, entities, role, preferences,
                       created_at, last_active, conversation_count
                FROM conversation_contexts
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return ConversationContext(
                user_id=row[0],
                session_id=row[1],
                entities=json.loads(row[2]),
                role=row[3],
                preferences=json.loads(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                last_active=datetime.fromisoformat(row[6]),
                conversation_count=row[7]
            )
    
    def _save_summary(self, summary: ConversationSummary):
        """Save conversation summary to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversation_summaries
                (session_id, user_id, start_time, end_time, message_count,
                 key_topics, entities_discussed, last_intent, summary_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary.session_id,
                summary.user_id,
                summary.start_time.isoformat(),
                summary.end_time.isoformat() if summary.end_time else None,
                summary.message_count,
                json.dumps(summary.key_topics),
                json.dumps(summary.entities_discussed),
                summary.last_intent,
                summary.summary_text
            ))
            conn.commit()
    
    def _generate_summary_text(self, messages: List[Dict], intents: List[str], 
                              context: ConversationContext) -> str:
        """Generate human-readable conversation summary."""
        # Simple summary generation (can be enhanced with LLM)
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        if len(user_messages) == 1:
            return f"Asked about {intents[0] if intents else 'treasury information'}"
        
        topics = ", ".join(set(intents))
        entities = ", ".join(context.entities)
        
        return (f"Discussed {topics} for entities: {entities}. "
                f"Total of {len(user_messages)} queries in this session.")


# Global instance
_memory_store: Optional[ConversationMemoryStore] = None


def get_memory_store() -> ConversationMemoryStore:
    """Get global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = ConversationMemoryStore()
    return _memory_store


def create_memory_store(db_path: str) -> ConversationMemoryStore:
    """Create new memory store with custom database path."""
    return ConversationMemoryStore(db_path)