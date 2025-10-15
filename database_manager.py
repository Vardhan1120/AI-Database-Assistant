"""
Database operations and management
"""

import sqlite3
import pandas as pd
import tempfile
import time
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import streamlit as st
from config import Config
from utils import Logger, Validator


class DatabaseManager:
    """Handle all database operations"""
    
    @staticmethod
    def create_from_csv(csv_file) -> Optional[str]:
        """Create SQLite database from CSV file"""
        try:
            # Read CSV with robust encoding fallbacks
            encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
            last_error = None
            df = None
            for enc in encodings_to_try:
                try:
                    # Reset file pointer between attempts
                    try:
                        csv_file.seek(0)
                    except Exception:
                        pass
                    df = pd.read_csv(csv_file, encoding=enc, on_bad_lines='skip', engine='python')
                    break
                except Exception as e:
                    last_error = e
                    continue
            if df is None:
                raise last_error if last_error else ValueError("Failed to read CSV with available encodings")
            
            if df.empty:
                st.error("❌ CSV file is empty")
                return None
            
            # Clean column names
            df.columns = (df.columns
                         .str.strip()
                         .str.replace(r'[^\w\s]', '_', regex=True)
                         .str.replace(r'\s+', '_', regex=True)
                         .str.lower())
            
            # Remove duplicate columns
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Create temporary database
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            conn = sqlite3.connect(temp_db.name)
            
            # Generate table name
            table_name = Path(csv_file.name).stem
            table_name = re.sub(r'[^\w]', '_', table_name).lower() or "data"
            
            # Write to database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            
            Logger.log(f"Database created from CSV: {table_name}")
            return temp_db.name
            
        except Exception as e:
            Logger.error("Error creating database from CSV", e)
            st.error(f"❌ Error processing CSV: {str(e)}")
            return None
    
    @staticmethod
    def get_schema(db_path: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Extract database schema and statistics"""
        conn = None
        try:
            if not db_path or not Path(db_path).exists():
                return None, None
            
            conn = sqlite3.connect(db_path, timeout=Config.DB_TIMEOUT)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            if not tables:
                return {}, {"total_tables": 0, "total_rows": 0, "total_columns": 0}
            
            schema_info = {}
            total_rows = 0
            total_columns = 0
            
            for (table_name,) in tables:
                try:
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cursor.fetchone()[0]
                    total_rows += row_count
                    total_columns += len(columns)
                    
                    # Get sample data for type inference
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                    sample = cursor.fetchone()
                    
                    schema_info[table_name] = {
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2] or "TEXT",
                                "notnull": bool(col[3]),
                                "pk": bool(col[5]),
                                "default": col[4]
                            }
                            for col in columns
                        ],
                        "row_count": row_count,
                        "has_data": sample is not None
                    }
                    
                except Exception as e:
                    Logger.error(f"Error reading table {table_name}", e)
                    continue
            
            db_stats = {
                "total_tables": len(schema_info),
                "total_rows": total_rows,
                "total_columns": total_columns,
                "database_size": Path(db_path).stat().st_size if Path(db_path).exists() else 0
            }
            
            Logger.log(f"Schema extracted: {len(schema_info)} tables, {total_rows} rows")
            return schema_info, db_stats
            
        except Exception as e:
            Logger.error("Error extracting schema", e)
            st.error(f"❌ Error reading database: {str(e)}")
            return None, None
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    @staticmethod
    def execute_query(query: str, db_path: str) -> Dict[str, Any]:
        """Execute SQL query safely"""
        conn = None
        try:
            # Validate query
            is_safe, message = Validator.is_safe_query(query)
            if not is_safe:
                return {"status": "error", "message": message}
            
            # Connect and execute
            conn = sqlite3.connect(db_path, timeout=Config.DB_TIMEOUT)
            cursor = conn.cursor()
            
            start_time = time.time()
            cursor.execute(query)
            execution_time = time.time() - start_time
            
            results = cursor.fetchall()
            
            if results:
                columns = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(results, columns=columns)
                
                Logger.log(f"Query executed: {len(df)} rows in {execution_time:.3f}s")
                
                return {
                    "status": "success",
                    "data": df,
                    "row_count": len(df),
                    "execution_time": execution_time,
                    "columns": columns
                }
            else:
                return {
                    "status": "success",
                    "data": pd.DataFrame(),
                    "row_count": 0,
                    "execution_time": execution_time,
                    "message": "Query executed successfully but returned no results"
                }
                
        except sqlite3.Error as e:
            Logger.error("Database error during query execution", e)
            return {"status": "error", "message": f"Database error: {str(e)}"}
        except Exception as e:
            Logger.error("Unexpected error during query execution", e)
            return {"status": "error", "message": f"Execution error: {str(e)}"}
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    @staticmethod
    def format_schema_for_prompt(schema: Dict) -> str:
        """Format schema for AI prompt"""
        if not schema:
            return "No schema available"
        
        schema_lines = ["DATABASE SCHEMA:\n"]
        
        for table_name, info in schema.items():
            row_count = info.get('row_count', 0)
            schema_lines.append(f"\nTable: {table_name} ({row_count:,} rows)")
            schema_lines.append("Columns:")
            
            for col in info.get('columns', []):
                pk = " [PRIMARY KEY]" if col.get('pk') else ""
                notnull = " [NOT NULL]" if col.get('notnull') else ""
                schema_lines.append(
                    f"  • {col.get('name')}: {col.get('type')}{pk}{notnull}"
                )
        
        return '\n'.join(schema_lines)
