#!/usr/bin/env python3
"""
Database repair script to fix corrupted JSON data
"""

import sqlite3
import json
import os

def repair_database():
    """Repair corrupted database data"""
    print("🔧 Repairing Database...")
    
    db_path = "adk_platform.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check agents table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        if not cursor.fetchone():
            print("❌ Agents table not found")
            return False
        
        # Get all agents
        cursor.execute("SELECT id, name, sub_agents, tools, model_settings, workflow_config, ui_config, tags FROM agents")
        agents = cursor.fetchall()
        
        print(f"✅ Found {len(agents)} agents to check")
        
        repaired_count = 0
        for agent in agents:
            agent_id, name, sub_agents, tools, model_settings, workflow_config, ui_config, tags = agent
            
            # Check and repair each JSON field
            fields_to_repair = [
                ('sub_agents', sub_agents, []),
                ('tools', tools, []),
                ('model_settings', model_settings, {}),
                ('workflow_config', workflow_config, {}),
                ('ui_config', ui_config, {}),
                ('tags', tags, [])
            ]
            
            for field_name, field_value, default_value in fields_to_repair:
                if field_value is not None:
                    try:
                        # Try to parse the JSON
                        json.loads(field_value)
                    except (json.JSONDecodeError, TypeError):
                        print(f"🔧 Repairing corrupted {field_name} for agent {name} (ID: {agent_id})")
                        
                        # Update with default value
                        cursor.execute(
                            f"UPDATE agents SET {field_name} = ? WHERE id = ?",
                            (json.dumps(default_value), agent_id)
                        )
                        repaired_count += 1
        
        # Commit changes
        conn.commit()
        print(f"✅ Repaired {repaired_count} corrupted fields")
        
        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM agents WHERE is_enabled = 1")
        enabled_count = cursor.fetchone()[0]
        print(f"✅ Enabled agents: {enabled_count}")
        
        conn.close()
        print("✅ Database repair completed")
        return True
        
    except Exception as e:
        print(f"❌ Database repair failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    repair_database()

