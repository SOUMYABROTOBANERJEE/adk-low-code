#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('adk_platform.db')
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if users table exists and has the right structure
    if ('users',) in tables:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nUsers table structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("\nUsers table does not exist!")
    
    conn.close()
    
except Exception as e:
    print(f"Error checking database: {e}")

