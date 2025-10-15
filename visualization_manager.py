"""
Data visualization management
"""

from typing import Dict, Optional, Any
import pandas as pd
import plotly.express as px
from config import Config
from utils import Logger, Validator


class VisualizationManager:
    """Handle data visualization"""
    
    @staticmethod
    def detect_opportunity(df: pd.DataFrame, query_type: str) -> Optional[Dict]:
        """Detect if data can be visualized"""
        try:
            if not Validator.validate_dataframe(df):
                return None
            
            if len(df) > Config.MAX_ROWS_VISUALIZATION:
                return None
            
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Skip if too many unique categories
            if categorical_cols:
                if all(df[col].nunique() > Config.MAX_UNIQUE_CATEGORIES for col in categorical_cols):
                    return None
            
            # Bar chart: categorical + numeric
            if numeric_cols and categorical_cols and len(df) <= 50:
                if df[categorical_cols[0]].nunique() <= Config.MAX_UNIQUE_CATEGORIES:
                    return {
                        "type": "bar",
                        "x": categorical_cols[0],
                        "y": numeric_cols[0],
                        "title": f"{numeric_cols[0]} by {categorical_cols[0]}"
                    }
            
            # Scatter plot: 2+ numeric columns
            if len(numeric_cols) >= 2 and len(df) <= 100:
                return {
                    "type": "scatter",
                    "x": numeric_cols[0],
                    "y": numeric_cols[1],
                    "title": f"{numeric_cols[1]} vs {numeric_cols[0]}"
                }
            
            # Line chart for time series
            date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            if date_cols and numeric_cols:
                return {
                    "type": "line",
                    "x": date_cols[0],
                    "y": numeric_cols[0],
                    "title": f"{numeric_cols[0]} over time"
                }
            
            return None
            
        except Exception as e:
            Logger.error("Error detecting visualization opportunity", e)
            return None
    
    @staticmethod
    def create(df: pd.DataFrame, config: Dict) -> Optional[Any]:
        """Create visualization from configuration"""
        try:
            viz_type = config.get("type")
            
            if viz_type == "bar":
                fig = px.bar(
                    df, 
                    x=config["x"], 
                    y=config["y"],
                    title=config["title"],
                    template="plotly_dark"
                )
            elif viz_type == "scatter":
                fig = px.scatter(
                    df, 
                    x=config["x"], 
                    y=config["y"],
                    title=config["title"],
                    template="plotly_dark"
                )
            elif viz_type == "line":
                fig = px.line(
                    df, 
                    x=config["x"], 
                    y=config["y"],
                    title=config["title"],
                    template="plotly_dark"
                )
            else:
                return None
            
            # Enhance layout
            fig.update_layout(
                height=400,
                hovermode='closest',
                showlegend=True,
                font=dict(size=12)
            )
            
            Logger.log(f"Visualization created: {viz_type}")
            return fig
            
        except Exception as e:
            Logger.error("Error creating visualization", e)
            return None
