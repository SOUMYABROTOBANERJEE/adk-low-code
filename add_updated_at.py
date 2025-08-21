#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('adk_platform.db')
    cursor = conn.cursor()
    
    # Add updated_at column if it doesn't exist
    cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    print("✅ Added updated_at column to users table")
    
    # Also add it to user_sessions table if needed
    try:
        cursor.execute("ALTER TABLE user_sessions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Added updated_at column to user_sessions table")
    except:
        print("ℹ️  updated_at column already exists in user_sessions table")
    
    conn.commit()
    conn.close()
    print("✅ Database schema updated successfully")
    
except Exception as e:
    print(f"Error updating database: {e}")

