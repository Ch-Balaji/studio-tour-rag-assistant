"""
Conversation memory management for the chatbot.
Handles storing and retrieving conversation history.
"""

from typing import List, Dict, Any, Optional
from collections import deque


class MemoryManager:
    """Manages conversation memory with a sliding window"""
    
    def __init__(self, max_turns: int = 5):
        """
        Initialize memory manager.
        
        Args:
            max_turns: Maximum number of conversation turns to keep
        """
        self.max_turns = max_turns
        self.conversation_history = deque(maxlen=max_turns * 2)  # *2 for user+assistant pairs
    
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to history.
        
        Args:
            message: User message text
        """
        self.conversation_history.append({
            'role': 'user',
            'content': message
        })
    
    def add_assistant_message(self, message: str) -> None:
        """
        Add an assistant message to history.
        
        Args:
            message: Assistant message text
        """
        self.conversation_history.append({
            'role': 'assistant',
            'content': message
        })
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the conversation history.
        
        Returns:
            List of message dictionaries
        """
        return list(self.conversation_history)
    
    def get_recent_context(self, num_turns: int = 3) -> str:
        """
        Get recent conversation as a formatted string.
        
        Args:
            num_turns: Number of recent turns to include
            
        Returns:
            Formatted conversation context
        """
        recent = list(self.conversation_history)[-(num_turns * 2):]
        
        context_parts = []
        for msg in recent:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def clear_history(self) -> None:
        """Clear all conversation history"""
        self.conversation_history.clear()
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the conversation.
        
        Returns:
            Dictionary with conversation stats
        """
        total_messages = len(self.conversation_history)
        user_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'user')
        assistant_messages = sum(1 for msg in self.conversation_history if msg['role'] == 'assistant')
        
        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'turns': min(user_messages, assistant_messages)
        }
    
    def export_history(self) -> List[Dict[str, str]]:
        """
        Export the entire conversation history.
        
        Returns:
            Complete conversation history
        """
        return self.get_history()
    
    def import_history(self, history: List[Dict[str, str]]) -> None:
        """
        Import conversation history.
        
        Args:
            history: List of message dictionaries to import
        """
        self.conversation_history.clear()
        for msg in history[-self.max_turns * 2:]:  # Keep only max_turns
            self.conversation_history.append(msg)

