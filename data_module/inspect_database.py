"""
Database Inspection Tool - View database structure and sample data
"""
import sqlite3
import pandas as pd
from datetime import datetime

def inspect_database(db_path: str = "data/portfolio.db"):
    """Inspect the portfolio database structure and data"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("PORTFOLIO DATABASE INSPECTION")
        print("=" * 60)
        
        # 1. List all tables
        print("\n1. DATABASE TABLES:")
        print("-" * 30)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  • {table[0]}")
        
        # 2. Show table schemas
        print("\n2. TABLE SCHEMAS:")
        print("-" * 30)
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name.upper()}:")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                pk_marker = " (PRIMARY KEY)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                print(f"  • {name}: {data_type}{null_marker}{pk_marker}")
        
        # 3. Show record counts
        print("\n3. RECORD COUNTS:")
        print("-" * 30)
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  • {table_name}: {count} records")
        
        # 4. Show sample data
        print("\n4. SAMPLE DATA:")
        print("-" * 30)
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            
            if rows:
                print(f"\n{table_name.upper()} (first 3 records):")
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Create DataFrame for better display
                df = pd.DataFrame(rows, columns=columns)
                print(df.to_string(index=False))
            else:
                print(f"\n{table_name.upper()}: No data")
        
        # 5. Show indexes
        print("\n5. DATABASE INDEXES:")
        print("-" * 30)
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
        if indexes:
            for idx in indexes:
                print(f"  • {idx[0]}")
        else:
            print("  No custom indexes found")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except FileNotFoundError:
        print(f"Database file not found: {db_path}")
        print("Run the portfolio tracker first to create the database.")

def show_database_size(db_path: str = "data/portfolio.db"):
    """Show database file size and storage usage"""
    import os
    
    try:
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_kb = size_bytes / 1024
            size_mb = size_kb / 1024
            
            print(f"\nDATABASE SIZE:")
            print(f"  File: {db_path}")
            print(f"  Size: {size_bytes:,} bytes ({size_kb:.2f} KB, {size_mb:.2f} MB)")
        else:
            print(f"Database file not found: {db_path}")
    except Exception as e:
        print(f"Error checking file size: {e}")

def export_table_to_csv(db_path: str = "data/portfolio.db", table_name: str = None):
    """Export table data to CSV"""
    try:
        conn = sqlite3.connect(db_path)
        
        if table_name:
            # Export specific table
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            csv_path = f"data/{table_name}_export.csv"
            df.to_csv(csv_path, index=False)
            print(f"Exported {table_name} to {csv_path}")
        else:
            # Export all tables
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                csv_path = f"data/{table_name}_export.csv"
                df.to_csv(csv_path, index=False)
                print(f"Exported {table_name} to {csv_path}")
        
        conn.close()
        
    except Exception as e:
        print(f"Export error: {e}")

if __name__ == "__main__":
    # Inspect the database
    inspect_database()
    
    # Show database size
    show_database_size()
    
    # Optionally export to CSV
    # export_table_to_csv()
