"""
AI integration for generating SQL queries and suggestions
"""

import json
import re
from typing import Dict, List, Optional, Any
import streamlit as st
from config import Config
from utils import Logger


class AIManager:
    """Manage AI client and interactions"""
    
    @staticmethod
    def initialize_client(api_key: str) -> Optional[Any]:
        """Initialize Gemini AI client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(Config.API_MODEL)
            Logger.log("AI client initialized successfully")
            return client
        except ImportError:
            st.error("❌ google-generativeai not installed. Run: pip install google-generativeai")
            return None
        except Exception as e:
            Logger.error("Failed to initialize AI client", e)
            st.error(f"❌ AI initialization error: {str(e)}")
            return None
    
    @staticmethod
    def generate_sql(client: Any, user_query: str, schema_text: str) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        try:
            prompt = f"""You are an expert SQL database analyst. Generate a precise SQLite query.

DATABASE SCHEMA:
{schema_text}

STRICT REQUIREMENTS:
1. ONLY generate SELECT queries
2. Use proper SQLite syntax and functions
3. For requests asking for "all" or "everything", DO NOT add LIMIT
4. For aggregations (COUNT, SUM, AVG, GROUP BY), DO NOT add LIMIT
5. For simple SELECT * queries without "all" in request, add LIMIT 1000
6. Use appropriate JOINs when querying multiple tables
7. Include meaningful column aliases for calculated fields
8. Optimize for performance

Return ONLY valid JSON (no markdown):
{{
    "status": "success",
    "sql_query": "YOUR_SQL_HERE",
    "explanation": "Brief explanation of what the query does",
    "query_type": "aggregation|filtering|join|simple_select|analytical",
    "estimated_complexity": "low|medium|high"
}}

If impossible to generate:
{{
    "status": "error",
    "message": "Clear explanation why query cannot be generated"
}}

USER QUESTION: {user_query}

JSON:"""

            response = client.generate_content(prompt)
            text = response.text.strip()
            
            # Clean response
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            result = json.loads(text)
            
            if isinstance(result, dict) and result.get("status") == "success":
                Logger.log(f"SQL generated successfully: {result.get('query_type')}")
                return result
            elif isinstance(result, dict):
                return result
            else:
                return {"status": "error", "message": "Invalid response format from AI"}
                
        except json.JSONDecodeError as e:
            Logger.error("JSON decode error in AI response", e)
            return {"status": "error", "message": "Failed to parse AI response"}
        except Exception as e:
            Logger.error("Error generating SQL", e)
            return {"status": "error", "message": f"AI error: {str(e)}"}
    
    @staticmethod
    def generate_suggestions(client: Any, schema: Dict) -> List[str]:
        """Generate smart query suggestions"""
        try:
            schema_summary = []
            for table, info in list(schema.items())[:5]:  # Limit to 5 tables
                cols = [col['name'] for col in info['columns'][:5]]
                schema_summary.append(f"{table}: {', '.join(cols)}")
            
            prompt = f"""Based on this database, suggest 3 insightful questions users might ask.

TABLES: {' | '.join(schema_summary)}

RULES:
- Questions must be under 15 words
- Focus on business insights and analytics
- Must be answerable with available data
- NO explanations or parentheses

Return ONLY JSON array:
["Question 1?", "Question 2?", "Question 3?"]

JSON:"""

            response = client.generate_content(prompt)
            text = response.text.strip().replace('```json', '').replace('```', '').strip()
            
            # Extract JSON array
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                text = text[start:end]
            
            suggestions = json.loads(text)
            
            if isinstance(suggestions, list) and suggestions:
                # Clean suggestions
                cleaned = []
                for s in suggestions[:3]:
                    clean = re.sub(r'\s*\([^)]*\)', '', str(s)).strip()
                    if clean:
                        cleaned.append(clean)
                return cleaned if cleaned else AIManager._get_default_suggestions()
            
            return AIManager._get_default_suggestions()
            
        except Exception as e:
            Logger.error("Error generating suggestions", e)
            return AIManager._get_default_suggestions()
    
    @staticmethod
    def _get_default_suggestions() -> List[str]:
        """Return default suggestions"""
        return [
            "Show me the first 10 rows of data",
            "What are the total record counts per table?",
            "Show summary statistics for numeric columns"
        ]
