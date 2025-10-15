"""
AI-Powered Database Assistant - Production Grade
A professional-grade application for natural language database querying with AI.

Features:
- Natural language to SQL conversion using Google Gemini AI
- Multi-session chat management with persistence
- Automatic data visualization
- CSV to SQLite conversion
- Export capabilities (CSV, JSON)
- Comprehensive error handling and logging
- Security features (SQL injection prevention, query validation)
"""

import streamlit as st

from config import Config, CUSTOM_CSS
from session_manager import SessionState
from ui_components import (
    render_header, render_sidebar, render_main_content, render_footer
)
from utils import Logger

# Page configuration
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    """Main application entry point"""
    try:
        # Initialize session state
        SessionState.initialize()
        
        # Render UI components
        render_header()
        render_sidebar()
        render_main_content()
        render_footer()
        
    except Exception as e:
        Logger.error("Critical error in main application", e)
        st.error(f"❌ Application error: {str(e)}")
        st.error("Please refresh the page to restart the application.")


if __name__ == "__main__":
    main()