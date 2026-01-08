"""
AI integration for generating SQL queries and suggestions
(using google-genai SDK only)
"""

import json
import re
from typing import Dict, List, Optional, Any

import streamlit as st
from google import genai

from config import Config
from utils import Logger


class AIManager:
    """Manage AI client and interactions"""

    @staticmethod
    def initialize_client(api_key: str) -> Optional[Any]:
        """Initialize Gemini AI client (google-genai, v1 API)"""
        try:
            client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "v1"}
            )

            Logger.log("Gemini AI client initialized successfully")
            return client

        except Exception as e:
            Logger.error("Failed to initialize Gemini AI client", e)
            st.error("❌ Failed to initialize AI client. Check API key.")
            return None

    @staticmethod
    def list_available_models(client: Any) -> List[str]:
        """List available models for debugging"""
        try:
            models = client.models.list()
            model_names = [model.name for model in models if hasattr(model, 'name')]
            Logger.log(f"Available models: {model_names}")
            return model_names
        except Exception as e:
            Logger.error("Failed to list models", e)
            return []

    @staticmethod
    def _try_generate_with_models(client: Any, prompt: str, model_names: List[str]) -> Optional[Any]:
        """Try to generate content with multiple model names"""
        for model_name in model_names:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                Logger.log(f"Successfully used model: {model_name}")
                return response
            except Exception as e:
                error_str = str(e)
                if "404" in error_str or "NOT_FOUND" in error_str:
                    Logger.log(f"Model {model_name} not found, trying next...")
                    continue
                else:
                    # Other errors, re-raise
                    raise
        return None

    @staticmethod
    def generate_sql(client: Any, user_query: str, schema_text: str) -> Dict[str, Any]:
        """Generate SQL query from natural language"""
        try:
            prompt = f"""
You are an expert SQLite database analyst.

DATABASE SCHEMA:
{schema_text}

STRICT RULES:
1. ONLY generate SELECT queries
2. Use valid SQLite syntax
3. For "all" or "everything", DO NOT add LIMIT
4. For aggregations (COUNT, SUM, AVG, GROUP BY), DO NOT add LIMIT
5. For simple SELECT * queries, add LIMIT 10
6. Use JOINs where required
7. Return ONLY valid JSON (no markdown)

JSON FORMAT:
{{
  "status": "success",
  "sql_query": "SQL_QUERY_HERE",
  "explanation": "Short explanation",
  "query_type": "aggregation|filtering|join|simple_select|analytical",
  "estimated_complexity": "low|medium|high"
}}

USER QUESTION:
{user_query}
"""

            # Try multiple model names as fallback
            model_names = [
                Config.API_MODEL,
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            response = AIManager._try_generate_with_models(client, prompt, model_names)
            
            if response is None:
                return {
                    "status": "error",
                    "message": "None of the tried models are available. Please check your API key and model availability."
                }

            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            result = json.loads(text)

            if isinstance(result, dict) and result.get("status") == "success":
                Logger.log(f"SQL generated successfully ({result.get('query_type')})")
                return result

            return {
                "status": "error",
                "message": result.get("message", "Invalid AI response")
            }

        except json.JSONDecodeError as e:
            Logger.error("JSON parsing failed for AI SQL response", e)
            return {
                "status": "error",
                "message": "AI returned invalid JSON"
            }

        except Exception as e:
            Logger.error("Error generating SQL with Gemini", e)
            error_msg = str(e)
            # If model not found, try to list available models
            if "404" in error_msg or "NOT_FOUND" in error_msg:
                try:
                    available_models = AIManager.list_available_models(client)
                    if available_models:
                        error_msg += f"\n\nAvailable models: {', '.join(available_models[:5])}"
                except Exception:
                    pass
            return {
                "status": "error",
                "message": f"AI error: {error_msg}"
            }

    @staticmethod
    def generate_suggestions(client: Any, schema: Dict) -> List[str]:
        """Generate smart query suggestions"""
        try:
            schema_summary = []
            for table, info in list(schema.items())[:5]:
                cols = [col["name"] for col in info["columns"][:5]]
                schema_summary.append(f"{table}: {', '.join(cols)}")

            prompt = f"""
Based on the database schema below, suggest 3 useful questions.

TABLES:
{' | '.join(schema_summary)}

RULES:
- Under 15 words each
- Must be answerable via SQL
- No explanations
- Return ONLY JSON array

FORMAT:
["Question 1?", "Question 2?", "Question 3?"]
"""

            # Try multiple model names as fallback
            model_names = [
                Config.API_MODEL,
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            response = AIManager._try_generate_with_models(client, prompt, model_names)
            
            if response is None:
                return AIManager._get_default_suggestions()

            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            suggestions = json.loads(text)

            if isinstance(suggestions, list):
                cleaned = []
                for s in suggestions[:3]:
                    clean = re.sub(r"\s*\([^)]*\)", "", str(s)).strip()
                    if clean:
                        cleaned.append(clean)

                if cleaned:
                    return cleaned

            return AIManager._get_default_suggestions()

        except Exception as e:
            Logger.error("Error generating AI suggestions", e)
            return AIManager._get_default_suggestions()

    @staticmethod
    def _get_default_suggestions() -> List[str]:
        """Fallback suggestions"""
        return [
            "Show me the first 10 rows of data",
            "What are the total record counts per table?",
            "Show summary statistics for numeric columns"
        ]
