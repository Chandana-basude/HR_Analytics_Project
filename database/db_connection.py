"""
HR Analytics System - Database Connection Module
"""
import mysql.connector
from mysql.connector import Error
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': os.environ.get('DB_NAME', 'hr_analytics'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'your_password_here'),
    'autocommit': True,
    'charset': 'utf8mb4'
}

def get_connection():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """
    Execute a SQL query.
    - fetch=False  → INSERT / UPDATE / DELETE  (returns lastrowid)
    - fetch=True   → SELECT                    (returns list of dicts)
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[QUERY ERROR] {e}")
        print(f"  Query : {query}")
        print(f"  Params: {params}")
        return None
    finally:
        cursor.close()
        conn.close()

def test_connection():
    conn = get_connection()
    if conn:
        print("[DB] Connection successful!")
        conn.close()
        return True
    print("[DB] Connection failed!")
    return False

if __name__ == "__main__":
    test_connection()
