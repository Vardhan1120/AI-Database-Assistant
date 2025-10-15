"""
Utility classes for logging and validation
"""

from datetime import datetime
from typing import Tuple
import pandas as pd
from config import Config


class Logger:
    """Simple logging utility"""
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    @staticmethod
    def error(message: str, exception: Exception = None):
        """Log error with optional exception"""
        Logger.log(f"ERROR: {message}", "ERROR")
        if exception:
            Logger.log(f"Exception: {str(exception)}", "ERROR")


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def is_safe_query(query: str) -> Tuple[bool, str]:
        """Validate SQL query for security"""
        if not query or not isinstance(query, str):
            return False, "Invalid query format"
        
        query_upper = query.upper().strip()
        
        # Check for dangerous keywords
        for keyword in Config.DANGEROUS_KEYWORDS:
            if keyword in query_upper.split():
                return False, f"Dangerous operation detected: {keyword}"
        
        # Must be SELECT query
        if not query_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        return True, "Query is safe"
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """Validate DataFrame"""
        return df is not None and isinstance(df, pd.DataFrame) and not df.empty
