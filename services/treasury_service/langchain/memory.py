"""
LangChain Memory Management for Treasury Agent.
"""
import sqlite3
from typing import Dict, List, Any, Optional
import json
import os


class TreasuryConversationMemory:
    """Persistent conversation memory using SQLite."""
    
    def __init__(self, db_path: str = "data/conversations.db", max_messages: int = 20):
        self.db_path = db_path
        self.max_messages = max_messages
        self._ensure_db_exists()
        
    def _ensure_db_exists(self):
        """Ensure database and table exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_id 
                ON conversations(conversation_id, timestamp)
            """)
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to the conversation history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations (conversation_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, role, content, json.dumps(metadata or {})))
            
        # Keep only last N messages
        self._trim_conversation(conversation_id)
    
    def get_messages(self, conversation_id: str, limit: int = None) -> List[Dict]:
        """Get messages for a conversation."""
        limit = limit or self.max_messages
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT role, content, metadata, timestamp
                FROM conversations
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))
            
            messages = []
            for row in reversed(cursor.fetchall()):  # Reverse to get chronological order
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'metadata': json.loads(row[2]) if row[2] else {},
                    'timestamp': row[3]
                })
                
        return messages
    
    def clear_conversation(self, conversation_id: str):
        """Clear all messages for a conversation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
    
    def _trim_conversation(self, conversation_id: str):
        """Keep only the last N messages for a conversation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM conversations
                WHERE conversation_id = ? AND id NOT IN (
                    SELECT id FROM conversations
                    WHERE conversation_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """, (conversation_id, conversation_id, self.max_messages))


class SimpleLangChainMemory:
    """Simple in-memory conversation storage compatible with LangChain patterns."""
    
    def __init__(self, k: int = 10):
        self.k = k  # Number of message pairs to keep
        self.messages = []
    
    def add_user_message(self, message: str):
        """Add a user message."""
        self.messages.append({"role": "user", "content": message})
        self._trim_messages()
    
    def add_ai_message(self, message: str):
        """Add an AI message."""
        self.messages.append({"role": "assistant", "content": message})
        self._trim_messages()
    
    def get_messages(self) -> List[Dict]:
        """Get all messages."""
        return self.messages.copy()
    
    def clear(self):
        """Clear all messages."""
        self.messages.clear()
    
    def _trim_messages(self):
        """Keep only the last k message pairs."""
        if len(self.messages) > self.k * 2:  # Each pair is user + assistant
            self.messages = self.messages[-(self.k * 2):]


def get_langchain_memory(**kwargs) -> SimpleLangChainMemory:
    """Get simplified LangChain-compatible memory instance for conversation."""
    # Accept any keyword arguments for API compatibility
    return SimpleLangChainMemory(k=10)  # Keep last 10 exchanges