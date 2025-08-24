#!/usr/bin/env python3
"""
Direct database test to check what's happening with agents
"""

import sqlite3
import json

def test_database_directly():
    """Test the database directly"""
    print("🔍 Testing Database Directly...")
    
    try:
        # Connect to database
        conn = sqlite3.connect("adk_platform.db")
        cursor = conn.cursor()
        
        # Check if agents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        table_exists = cursor.fetchone()
        print(f"✅ Agents table exists: {table_exists is not None}")
        
        if table_exists:
            # Check table structure
            cursor.execute("PRAGMA table_info(agents)")
            columns = cursor.fetchall()
            print(f"✅ Agents table columns: {[col[1] for col in columns]}")
            
            # Check if there are any agents
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            print(f"✅ Total agents in database: {count}")
            
            # Check enabled agents
            cursor.execute("SELECT COUNT(*) FROM agents WHERE is_enabled = 1")
            enabled_count = cursor.fetchone()[0]
            print(f"✅ Enabled agents: {enabled_count}")
            
            # Get sample agent data
            cursor.execute("SELECT * FROM agents LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"✅ Sample agent data: {sample}")
                
                # Check sub_agents field specifically
                cursor.execute("SELECT id, name, sub_agents FROM agents LIMIT 1")
                agent_data = cursor.fetchone()
                if agent_data:
                    print(f"✅ Agent sub_agents field: {agent_data[2]}")
                    try:
                        if agent_data[2]:
                            parsed = json.loads(agent_data[2])
                            print(f"✅ Parsed sub_agents: {parsed}")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
            else:
                print("⚠️  No agents found in database")
        
        conn.close()
        print("✅ Database test completed")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_directly()

