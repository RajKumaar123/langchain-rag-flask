"""
Simple per-session ConversationBufferMemory registry.
For production, replace with Redis or DB-backed memory keyed by session id.
"""
from langchain.memory import ConversationBufferMemory

_memory_registry = {}

def get_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _memory_registry:
        _memory_registry[session_id] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return _memory_registry[session_id]
