"""
Configuration constants for the AI Database Assistant
"""

class Config:
    """Application configuration"""
    APP_TITLE = "AI Database Assistant"
    APP_ICON = "🤖"
    LAYOUT = "wide"
    MAX_ROWS_DISPLAY = 1000
    MAX_ROWS_VISUALIZATION = 500
    MAX_UNIQUE_CATEGORIES = 20
    DB_TIMEOUT = 30
    API_MODEL = "gemini-2.5-flash"


    
    # Security
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 
        'CREATE', 'INSERT', 'UPDATE', 'REPLACE',
        'ATTACH', 'DETACH', 'PRAGMA'
    ]

# Custom CSS for dark theme
CUSTOM_CSS = """
<style>
    /* Global dark theme */
    .stAppViewContainer, .stApp, body {
        background: #000 !important;
        color: #eaeaea !important;
    }
    a { color: #7bb4ff !important; }
    hr { border-color: #333; }

    /* Main styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        color: #fff; /* Fallback for browsers without background-clip support */
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #000;
        color: #eaeaea;
    }
    section[data-testid="stSidebar"] * {
        color: #eaeaea !important;
    }
    section[data-testid="stSidebar"] a {
        color: #7bb4ff !important; /* Accessible link color */
    }
    section[data-testid="stSidebar"] .stButton>button {
        background: #111;
        color: #eaeaea;
        border: 1px solid #333;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: #1a1a1a;
        color: #fff;
        box-shadow: none;
    }

    .sub-header {
        color: #bbb;
        font-size: 1.15rem;
        margin-bottom: 2rem;
        text-align: center;
        line-height: 1.6;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid #333;
        background: #111;
    }
    
    /* Metrics styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #111 0%, #222 100%);
        padding: 15px;
        border-radius: 10px;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: #0d0d0d;
        border: 1px solid #222;
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 8px;
        background: #111 !important;
        color: #eaeaea !important;
    }
    
    /* Success/Error/Warning messages */
    .element-container .stAlert {
        border-radius: 10px;
        background: #111;
        color: #eaeaea;
        border: 1px solid #333;
    }
</style>
"""
