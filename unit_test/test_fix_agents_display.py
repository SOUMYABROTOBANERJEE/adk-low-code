#!/usr/bin/env python3
"""
Script to fix agents display issue by checking database and creating sample agents
"""

import sqlite3
import json
import uuid
from datetime import datetime

def check_and_fix_agents():
    """Check database and create sample agents if needed"""
    print("🔍 Checking Database and Agents...")
    
    try:
        # Connect to database
        conn = sqlite3.connect("adk_platform.db")
        cursor = conn.cursor()
        
        # Check if agents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        if not cursor.fetchone():
            print("❌ Agents table does not exist!")
            return False
        
        # Check current agents count
        cursor.execute("SELECT COUNT(*) FROM agents WHERE is_enabled = 1")
        enabled_count = cursor.fetchone()[0]
        print(f"✅ Current enabled agents: {enabled_count}")
        
        # Check all agents (including disabled)
        cursor.execute("SELECT COUNT(*) FROM agents")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total agents (all): {total_count}")
        
        if enabled_count == 0:
            print("🔧 No enabled agents found. Creating sample agents...")
            
            # Create sample agents
            sample_agents = [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Sample Assistant',
                    'description': 'A helpful assistant agent',
                    'agent_type': 'basic',
                    'system_prompt': 'You are a helpful AI assistant.',
                    'instructions': 'Help users with their questions.',
                    'sub_agents': json.dumps([]),
                    'tools': json.dumps([]),
                    'model_settings': json.dumps({"model": "gemini-1.5-pro", "temperature": 0.7}),
                    'workflow_config': json.dumps({}),
                    'ui_config': json.dumps({"position": {"x": 100, "y": 100}}),
                    'tags': json.dumps(["assistant", "sample"]),
                    'version': '1.0.0',
                    'is_enabled': 1
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Code Helper',
                    'description': 'An agent that helps with coding tasks',
                    'agent_type': 'basic',
                    'system_prompt': 'You are a coding assistant.',
                    'instructions': 'Help users with programming questions.',
                    'sub_agents': json.dumps([]),
                    'tools': json.dumps([]),
                    'model_settings': json.dumps({"model": "gemini-1.5-pro", "temperature": 0.3}),
                    'workflow_config': json.dumps({}),
                    'ui_config': json.dumps({"position": {"x": 200, "y": 100}}),
                    'tags': json.dumps(["coding", "sample"]),
                    'version': '1.0.0',
                    'is_enabled': 1
                }
            ]
            
            for agent in sample_agents:
                cursor.execute('''
                    INSERT INTO agents (
                        id, name, description, agent_type, system_prompt,
                        instructions, sub_agents, tools, model_settings,
                        workflow_config, ui_config, tags, version, is_enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent['id'], agent['name'], agent['description'], 
                    agent['agent_type'], agent['system_prompt'], agent['instructions'],
                    agent['sub_agents'], agent['tools'], agent['model_settings'],
                    agent['workflow_config'], agent['ui_config'], agent['tags'],
                    agent['version'], agent['is_enabled']
                ))
                print(f"✅ Created agent: {agent['name']}")
            
            conn.commit()
            print("✅ Sample agents created successfully!")
        
        # Verify agents after creation
        cursor.execute("SELECT COUNT(*) FROM agents WHERE is_enabled = 1")
        final_count = cursor.fetchone()[0]
        print(f"✅ Final enabled agents count: {final_count}")
        
        # Show sample of agents
        cursor.execute("SELECT id, name, description FROM agents WHERE is_enabled = 1 LIMIT 3")
        agents = cursor.fetchall()
        print("📋 Sample agents:")
        for agent_id, name, desc in agents:
            print(f"   - {name}: {desc} (ID: {agent_id[:8]}...)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if check_and_fix_agents():
        print("\n✅ Database check and fix completed!")
        print("🔄 Now restart your server and try the frontend again.")
    else:
        print("\n❌ Failed to fix database issues.")
