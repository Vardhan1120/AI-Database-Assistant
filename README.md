# AI Database Assistant

A professional-grade Streamlit application for natural language database querying with AI.

## Features

- 🤖 **AI-Powered Query Generation** - Convert natural language to optimized SQL using Google Gemini AI
- 💬 **Multi-Session Management** - Save and switch between multiple chat sessions
- 📊 **Single & Batch CSV Processing** - Upload individual files or entire folders of CSV files
- 📈 **Automatic Visualizations** - Smart chart generation based on data patterns
- 💾 **Export Capabilities** - Download results as CSV or chat history as JSON
- 🔒 **Enterprise Security** - Built-in SQL injection prevention and query validation
- 📊 **Real-time Statistics** - Track queries, sessions, and performance metrics
- 📁 **Folder Upload Support** - Process multiple CSV files simultaneously with progress tracking

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Get your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. Upload a database file (.db, .sqlite) or CSV file

4. Start asking questions in natural language!

## Project Structure

```
├── app.py                 # Main application entry point
├── config.py              # Configuration constants and CSS
├── utils.py               # Logger and Validator utilities
├── ai_manager.py          # AI integration for SQL generation
├── database_manager.py    # Database operations and management
├── visualization_manager.py # Data visualization handling
├── session_manager.py     # Chat session management
├── ui_components.py       # UI rendering functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```



## Security Features

- Only SELECT queries are allowed
- SQL injection prevention
- Query validation and sanitization
- Local data processing


