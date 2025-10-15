"""
UI components and rendering functions
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict
import pandas as pd
import streamlit as st

from config import Config
from utils import Logger, Validator
from ai_manager import AIManager
from database_manager import DatabaseManager
from visualization_manager import VisualizationManager
from session_manager import ChatSessionManager, SessionState


def render_header():
    """Render application header"""
    st.markdown(
        f'<p class="main-header">{Config.APP_ICON} {Config.APP_TITLE}</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-header">Transform natural language into SQL queries with AI • '
        'Upload databases or CSV files • Visualize insights instantly • Enterprise-grade security</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render sidebar with all controls"""
    with st.sidebar:
        # Header
        st.image("https://img.icons8.com/fluency/96/database.png", width=80)
        st.title("⚙️ Control Panel")
        
        # Chat Sessions
        render_chat_sessions()
        
        st.divider()
        
        # API Configuration
        render_api_config()
        
        st.divider()
        
        # File Upload
        render_file_upload()
        
        st.divider()
        
        # Database Schema
        render_schema_viewer()
        
        st.divider()
        
        # Action Buttons
        render_action_buttons()
        
        st.divider()
        
        # Statistics
        render_statistics()


def render_chat_sessions():
    """Render chat session management"""
    st.subheader("💬 Chat Sessions")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        ChatSessionManager.create_new()
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.chat_sessions:
        st.markdown(f"**Recent Chats** ({len(st.session_state.chat_sessions)})")
        
        for session in st.session_state.chat_sessions[:10]:
            is_current = session.get("id") == st.session_state.current_session_id
            msg_count = session.get("message_count", 0)
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                icon = "📌" if is_current else "💬"
                label = f"{icon} {session.get('title', 'Chat')}"
                if st.button(
                    label,
                    key=f"load_{session.get('id')}",
                    use_container_width=True,
                    disabled=is_current,
                    help=f"{msg_count} messages • {session.get('timestamp', '')}"
                ):
                    ChatSessionManager.load(session.get("id"))
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{session.get('id')}", help="Delete chat"):
                    ChatSessionManager.delete(session.get("id"))
                    st.rerun()
            
            st.caption(f"🕐 {session.get('timestamp', '')} • 💬 {msg_count} messages")
    else:
        st.info("No saved chats yet. Start chatting!")


def render_api_config():
    """Render API configuration section"""
    st.subheader("🔑 API Configuration")
    
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Get your free API key from Google AI Studio",
        value="" if not st.session_state.api_configured else "••••••••••••••••",
        placeholder="Enter your API key here"
    )
    
    if api_key and not api_key.startswith("••"):
        client = AIManager.initialize_client(api_key)
        if client:
            st.session_state.genai_client = client
            st.session_state.api_configured = True
            st.success("✅ API Connected Successfully!")
    elif st.session_state.api_configured:
        st.success("✅ API Connected")
    else:
        st.info("👆 Enter your Gemini API key to get started")
        with st.expander("❓ How to get API Key"):
            st.markdown("""
            ### Get Your Free Gemini API Key
            
            1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
            2. Sign in with your Google account
            3. Click **"Create API Key"**
            4. Copy the key and paste it above
            
            **Note:** The API is free with generous quotas!
            """)


def render_file_upload():
    """Render file upload section"""
    st.subheader("📁 Data Source")
    
    uploaded_file = st.file_uploader(
        "Upload Database or CSV",
        type=['db', 'sqlite', 'csv'],
        help="Supported formats: SQLite (.db, .sqlite) or CSV files",
        key="db_uploader"
    )
    
    if uploaded_file:
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        with st.spinner("🔄 Processing file..."):
            try:
                if file_extension == '.csv':
                    db_path = DatabaseManager.create_from_csv(uploaded_file)
                else:
                    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
                    temp_db.write(uploaded_file.read())
                    temp_db.close()
                    db_path = temp_db.name
                
                if db_path:
                    st.session_state.db_path = db_path
                    schema, stats = DatabaseManager.get_schema(db_path)
                    
                    if schema and stats:
                        st.session_state.db_schema = schema
                        st.session_state.db_stats = stats
                        
                        st.success(f"✅ Successfully loaded: {uploaded_file.name}")
                        
                        # Display statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 Tables", stats['total_tables'])
                        with col2:
                            st.metric("📝 Rows", f"{stats['total_rows']:,}")
                        with col3:
                            st.metric("🔢 Columns", stats['total_columns'])
                        
                        # Generate suggestions if AI is configured
                        if st.session_state.genai_client and not st.session_state.suggested_queries:
                            with st.spinner("🤖 Generating smart suggestions..."):
                                st.session_state.suggested_queries = AIManager.generate_suggestions(
                                    st.session_state.genai_client,
                                    schema
                                )
                    else:
                        st.error("❌ Could not read database schema")
                        
            except Exception as e:
                Logger.error("Error during file upload", e)
                st.error(f"❌ Error processing file: {str(e)}")


def render_schema_viewer():
    """Render database schema viewer"""
    if st.session_state.db_schema:
        st.subheader("📊 Database Schema")
        
        with st.expander("View Schema Details", expanded=False):
            for table_name, info in st.session_state.db_schema.items():
                st.markdown(f"### 🗂️ {table_name}")
                st.caption(f"📊 {info.get('row_count', 0):,} rows")
                
                try:
                    col_data = pd.DataFrame([
                        {
                            "Column": col.get('name', ''),
                            "Type": col.get('type', ''),
                            "Primary Key": "✓" if col.get('pk') else "",
                            "Not Null": "✓" if col.get('notnull') else ""
                        }
                        for col in info.get('columns', [])
                    ])
                    st.dataframe(
                        col_data,
                        hide_index=True,
                        use_container_width=True
                    )
                except Exception as e:
                    st.caption(f"Error displaying schema: {str(e)}")
                
                st.markdown("---")


def render_action_buttons():
    """Render action buttons"""
    st.subheader("🎯 Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, help="Clear current chat"):
            SessionState.reset_chat()
            st.rerun()
    
    with col2:
        if st.button("📥 Export", use_container_width=True, help="Export chat history"):
            if st.session_state.messages:
                try:
                    export_data = {
                        "session_id": st.session_state.current_session_id,
                        "timestamp": datetime.now().isoformat(),
                        "messages": [],
                        "query_history": st.session_state.query_history,
                        "total_queries": len(st.session_state.query_history)
                    }
                    
                    for msg in st.session_state.messages:
                        clean_msg = {
                            "role": str(msg.get("role", "")),
                            "content": str(msg.get("content", ""))
                        }
                        if "sql_query" in msg:
                            clean_msg["sql_query"] = str(msg.get("sql_query", ""))
                        if "execution_time" in msg:
                            clean_msg["execution_time"] = float(msg.get("execution_time", 0))
                        export_data["messages"].append(clean_msg)
                    
                    chat_export = json.dumps(export_data, indent=2)
                    st.download_button(
                        "💾 Download JSON",
                        chat_export,
                        f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                        use_container_width=True,
                        key="download_chat_btn"
                    )
                except Exception as e:
                    Logger.error("Error exporting chat", e)
                    st.error(f"Export error: {str(e)}")
            else:
                st.info("No chat to export")


def render_statistics():
    """Render application statistics"""
    st.subheader("📈 Statistics")
    
    uptime = datetime.now() - st.session_state.app_start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    stats_data = {
        "⏱️ Session Time": f"{hours}h {minutes}m",
        "🔍 Queries Run": st.session_state.total_queries_executed,
        "💬 Chat Sessions": len(st.session_state.chat_sessions),
        "📊 Current Messages": len(st.session_state.messages)
    }
    
    for label, value in stats_data.items():
        st.metric(label, value)


def render_main_content():
    """Render main content area"""
    if not st.session_state.api_configured:
        render_welcome_screen()
    elif not st.session_state.db_path:
        render_upload_prompt()
    else:
        render_chat_interface()


def render_welcome_screen():
    """Render welcome screen when API is not configured"""
    st.warning("⚠️ Please configure your Gemini API key in the sidebar to get started.")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Natural Language Queries")
        st.write("Ask questions in plain English - no SQL knowledge required. The AI understands your intent.")
    
    with col2:
        st.markdown("### 📊 Smart Visualizations")
        st.write("Automatic chart generation for suitable datasets. Get insights at a glance.")
    
    with col3:
        st.markdown("### 🔒 Enterprise Security")
        st.write("Built-in SQL injection prevention, query validation, and safe execution.")
    
    st.markdown("---")
    
    st.markdown("### 🌟 Key Features")
    features = [
        "✅ **AI-Powered Query Generation** - Convert natural language to optimized SQL",
        "✅ **Multi-Session Management** - Save and switch between multiple chat sessions",
        "✅ **CSV to SQLite Conversion** - Instant database creation from CSV files",
        "✅ **Automatic Visualizations** - Smart chart generation based on data patterns",
        "✅ **Export Capabilities** - Download results as CSV or chat history as JSON",
        "✅ **Production-Ready** - Comprehensive error handling and logging",
        "✅ **Real-time Statistics** - Track queries, sessions, and performance metrics"
    ]
    
    for feature in features:
        st.markdown(feature)


def render_upload_prompt():
    """Render upload prompt when no database is loaded"""
    st.info("📤 Please upload a database file or CSV in the sidebar to begin analyzing data.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Supported Formats")
        st.markdown("""
        - **SQLite Database** (.db, .sqlite)
        - **CSV Files** (.csv)
        
        Upload any of these formats to get started!
        """)
    
    with col2:
        st.markdown("### 🚀 What You Can Do")
        st.markdown("""
        - Ask questions in natural language
        - Generate complex SQL queries
        - Visualize data automatically
        - Export results and insights
        """)
    

def render_chat_interface():
    """Render main chat interface"""
    if not st.session_state.current_session_id:
        ChatSessionManager.create_new()
    
    # Suggested queries
    if st.session_state.suggested_queries:
        with st.expander("💡 Suggested Questions", expanded=False):
            st.markdown("**Click to copy any question below:**")
            cols = st.columns(len(st.session_state.suggested_queries))
            for idx, (col, suggestion) in enumerate(zip(cols, st.session_state.suggested_queries)):
                with col:
                    st.code(suggestion, language=None)
    
    st.divider()
    
    # Display chat messages
    for idx, message in enumerate(st.session_state.messages):
        render_chat_message(message, idx)
    
    # Chat input
    st.divider()
    st.markdown("**💬 Ask a question about your data:**")
    
    if prompt := st.chat_input("Type your question here...", key="chat_input"):
        handle_user_input(prompt)


def render_chat_message(message: Dict, idx: int):
    """Render a single chat message"""
    try:
        with st.chat_message(message.get("role", "user")):
            st.markdown(str(message.get("content", "")))
            
            # Show SQL query if present
            if message.get("sql_query"):
                with st.expander("🔍 SQL Query", expanded=False):
                    st.code(str(message["sql_query"]), language="sql")
                    if "execution_time" in message:
                        st.caption(f"⚡ Executed in {message['execution_time']:.3f} seconds")
            
            # Show dataframe if present
            if "dataframe" in message:
                df = message.get("dataframe")
                if Validator.validate_dataframe(df):
                    render_dataframe_results(df, idx)
                    
                    # Show visualization if available
                    if "visualization" in message and message["visualization"]:
                        try:
                            st.plotly_chart(
                                message["visualization"],
                                use_container_width=True,
                                key=f"viz_{idx}"
                            )
                        except Exception as e:
                            Logger.error("Error rendering visualization", e)
                            
    except Exception as e:
        Logger.error("Error rendering message", e)
        st.error(f"Error displaying message: {str(e)}")


def render_dataframe_results(df: pd.DataFrame, idx: int):
    """Render dataframe with controls"""
    try:
        row_count = len(df)
        
        # Pagination for large datasets
        if row_count > Config.MAX_ROWS_DISPLAY:
            show_all = st.checkbox(
                f"Show all {row_count:,} rows",
                key=f"show_all_{idx}",
                help="Warning: May slow down the interface"
            )
            df_display = df if show_all else df.head(Config.MAX_ROWS_DISPLAY)
            if not show_all:
                st.info(f"📊 Showing first {Config.MAX_ROWS_DISPLAY:,} of {row_count:,} rows")
        else:
            df_display = df
        
        # Display dataframe
        st.dataframe(
            df_display,
            use_container_width=True,
            height=min(400, len(df_display) * 35 + 38)
        )
        
        # Action buttons and metrics
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            try:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"query_results_{row_count}_rows.csv",
                    "text/csv",
                    key=f"dl_csv_{idx}"
                )
            except Exception as e:
                Logger.error("Error creating CSV download", e)
        
        with col2:
            st.metric("📊 Rows", f"{row_count:,}")
        
        with col3:
            st.metric("🔢 Columns", len(df.columns))
        
        with col4:
            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
            st.metric("💾 Size", f"{memory_usage:.2f} MB")
            
    except Exception as e:
        Logger.error("Error rendering dataframe results", e)
        st.error(f"Error displaying results: {str(e)}")


def handle_user_input(prompt: str):
    """Handle user input and generate response"""
    try:
        # Save current session
        if st.session_state.messages:
            ChatSessionManager.save_current()
        
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your question..."):
                process_query(prompt)
        
        # Save session and increment counter
        st.session_state.total_queries_executed += 1
        ChatSessionManager.save_current()
        st.rerun()
        
    except Exception as e:
        Logger.error("Error handling user input", e)
        st.error(f"❌ Error processing your question: {str(e)}")


def process_query(prompt: str):
    """Process user query and execute SQL"""
    try:
        # Format schema for AI
        schema_text = DatabaseManager.format_schema_for_prompt(st.session_state.db_schema)
        
        # Generate SQL query
        sql_result = AIManager.generate_sql(
            st.session_state.genai_client,
            prompt,
            schema_text
        )
        
        if sql_result.get("status") == "success":
            sql_query = sql_result.get("sql_query", "")
            explanation = sql_result.get("explanation", "Query executed")
            query_type = sql_result.get("query_type", "simple_select")
            complexity = sql_result.get("estimated_complexity", "medium")
            
            # Display explanation
            st.markdown(f"**{explanation}**")
            if complexity == "high":
                st.warning("⚠️ Complex query detected - may take longer to execute")
            
            # Show SQL query
            with st.expander("🔍 Generated SQL Query", expanded=False):
                st.code(sql_query, language="sql")
                st.caption(f"Query Type: {query_type} | Complexity: {complexity}")
            
            # Execute query
            with st.spinner("⚡ Executing query..."):
                exec_result = DatabaseManager.execute_query(
                    sql_query,
                    st.session_state.db_path
                )
            
            if exec_result.get("status") == "success":
                handle_successful_query(
                    exec_result,
                    sql_query,
                    explanation,
                    query_type
                )
            else:
                handle_query_error(exec_result, sql_query, explanation)
        else:
            error_msg = sql_result.get("message", "Failed to generate SQL query")
            st.error(f"❌ {error_msg}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Could not generate query: {error_msg}",
                "dataframe": None
            })
            
    except Exception as e:
        Logger.error("Error processing query", e)
        st.error(f"❌ Error: {str(e)}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Processing error: {str(e)}",
            "dataframe": None
        })


def handle_successful_query(exec_result: Dict, sql_query: str, explanation: str, query_type: str):
    """Handle successful query execution"""
    df = exec_result.get("data")
    row_count = exec_result.get("row_count", 0)
    exec_time = exec_result.get("execution_time", 0)
    
    if row_count > 0:
        # Show success message
        if row_count > 5000:
            st.warning(f"⚠️ Large result set: {row_count:,} rows")
        else:
            st.success(f"✅ Query successful! Found {row_count:,} row(s) in {exec_time:.3f} seconds")
        
        # Display results
        render_dataframe_results(df, len(st.session_state.messages))
        
        # Generate visualization if applicable
        viz_fig = None
        if row_count <= Config.MAX_ROWS_VISUALIZATION:
            viz_config = VisualizationManager.detect_opportunity(df, query_type)
            if viz_config:
                viz_fig = VisualizationManager.create(df, viz_config)
                if viz_fig:
                    st.plotly_chart(viz_fig, use_container_width=True)
                    st.caption("📊 Automatic visualization generated based on your data")
        
        # Save to history
        st.session_state.query_history.append({
            "question": st.session_state.messages[-1].get("content"),
            "sql": sql_query,
            "rows_returned": row_count,
            "execution_time": exec_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to messages
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**{explanation}**\n\n✅ Found {row_count:,} row(s) in {exec_time:.3f} seconds",
            "sql_query": sql_query,
            "dataframe": df,
            "execution_time": exec_time,
            "visualization": viz_fig
        })
    else:
        st.info(f"ℹ️ Query executed successfully in {exec_time:.3f} seconds but returned no results")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**{explanation}**\n\nℹ️ No results found",
            "sql_query": sql_query,
            "dataframe": None,
            "execution_time": exec_time
        })


def handle_query_error(exec_result: Dict, sql_query: str, explanation: str):
    """Handle query execution errors"""
    error_msg = exec_result.get("message", "Unknown error occurred")
    st.error(f"❌ Query failed: {error_msg}")
    
    with st.expander("🔍 Failed SQL Query"):
        st.code(sql_query, language="sql")
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"**{explanation}**\n\n❌ Error: {error_msg}",
        "sql_query": sql_query,
        "dataframe": None
    })


def render_footer():
    """Render application footer"""
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #ddd; padding: 20px; background:#000;'>
        <p style='font-size: 1.1em;'><strong>🚀 Powered by Google Gemini AI</strong></p>
        <p style='font-size: 0.95em;'>
            🔒 Your data is processed locally • 
        </p>
        <p style='font-size: 0.85em; color: #aaa;'>
            Version 1.0.0 | © 2025 AI Database Assistant
        </p>
    </div>
    """, unsafe_allow_html=True)
