"""
Chat session management
"""

import time
from datetime import datetime
import streamlit as st
from utils import Logger


class ChatSessionManager:
    """Manage chat sessions"""
    
    @staticmethod
    def create_new():
        """Create a new chat session"""
        try:
            session_id = f"session_{st.session_state.session_counter}_{int(time.time())}"
            st.session_state.session_counter += 1
            
            if st.session_state.current_session_id and st.session_state.messages:
                ChatSessionManager.save_current()
            
            st.session_state.current_session_id = session_id
            st.session_state.messages = []
            st.session_state.query_history = []
            
            Logger.log(f"New chat session created: {session_id}")
            
        except Exception as e:
            Logger.error("Error creating new chat session", e)
            st.error(f"Error creating new chat: {str(e)}")
    
    @staticmethod
    def save_current():
        """Save the current chat session"""
        try:
            if not st.session_state.messages:
                return
            
            # Generate title from first user message
            title = "New Chat"
            for msg in st.session_state.messages:
                if msg.get("role") == "user":
                    content = str(msg.get("content", ""))
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    break
            
            session_data = {
                "id": st.session_state.current_session_id,
                "title": title,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": [],
                "query_history": st.session_state.query_history.copy(),
                "message_count": sum(1 for m in st.session_state.messages if m.get("role") == "user")
            }
            
            # Clean messages (remove DataFrames for serialization)
            for msg in st.session_state.messages:
                clean_msg = {
                    "role": msg.get("role", ""),
                    "content": str(msg.get("content", ""))
                }
                if "sql_query" in msg:
                    clean_msg["sql_query"] = str(msg["sql_query"])
                if "execution_time" in msg:
                    clean_msg["execution_time"] = float(msg["execution_time"])
                session_data["messages"].append(clean_msg)
            
            # Update or add session
            existing_index = next(
                (i for i, s in enumerate(st.session_state.chat_sessions) 
                 if s.get("id") == st.session_state.current_session_id),
                None
            )
            
            if existing_index is not None:
                st.session_state.chat_sessions[existing_index] = session_data
            else:
                st.session_state.chat_sessions.insert(0, session_data)
            
            # Limit to 50 sessions
            if len(st.session_state.chat_sessions) > 50:
                st.session_state.chat_sessions = st.session_state.chat_sessions[:50]
            
            Logger.log(f"Session saved: {session_data['id']}")
            
        except Exception as e:
            Logger.error("Error saving session", e)
    
    @staticmethod
    def load(session_id: str):
        """Load a specific chat session"""
        try:
            if st.session_state.current_session_id and st.session_state.messages:
                ChatSessionManager.save_current()
            
            session = next(
                (s for s in st.session_state.chat_sessions if s.get("id") == session_id),
                None
            )
            
            if session:
                st.session_state.current_session_id = session_id
                st.session_state.messages = session.get("messages", []).copy()
                st.session_state.query_history = session.get("query_history", []).copy()
                Logger.log(f"Session loaded: {session_id}")
            
        except Exception as e:
            Logger.error("Error loading session", e)
            st.error(f"Error loading session: {str(e)}")
    
    @staticmethod
    def delete(session_id: str):
        """Delete a chat session"""
        try:
            st.session_state.chat_sessions = [
                s for s in st.session_state.chat_sessions 
                if s.get("id") != session_id
            ]
            
            if st.session_state.current_session_id == session_id:
                ChatSessionManager.create_new()
            
            Logger.log(f"Session deleted: {session_id}")
            
        except Exception as e:
            Logger.error("Error deleting session", e)
            st.error(f"Error deleting session: {str(e)}")


class SessionState:
    """Centralized session state management"""
    
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        defaults = {
            'messages': [],
            'db_path': None,
            'db_schema': None,
            'genai_client': None,
            'query_history': [],
            'suggested_queries': [],
            'db_stats': None,
            'chat_sessions': [],
            'current_session_id': None,
            'session_counter': 0,
            'api_configured': False,
            'total_queries_executed': 0,
            'app_start_time': datetime.now()
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Auto-initialize API client from secrets if available
        if not st.session_state.api_configured:
            try:
                from ai_manager import AIManager
                if hasattr(st, 'secrets') and st.secrets:
                    secret_api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini_api_key")
                    if secret_api_key:
                        client = AIManager.initialize_client(secret_api_key)
                        if client:
                            st.session_state.genai_client = client
                            st.session_state.api_configured = True
            except Exception:
                pass  # Secrets not configured or error, that's okay
    
    @staticmethod
    def reset_chat():
        """Reset chat-specific state"""
        st.session_state.messages = []
        st.session_state.query_history = []
    
    @staticmethod
    def clear_database():
        """Clear database-specific state"""
        st.session_state.db_path = None
        st.session_state.db_schema = None
        st.session_state.db_stats = None
        st.session_state.suggested_queries = []
