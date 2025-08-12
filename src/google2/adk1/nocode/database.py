"""
Database layer for the Google ADK No-Code Platform
Supports SQLite for development and can be easily migrated to GCP Firestore/BigQuery
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for storing agents, tools, and projects"""
    
    def __init__(self, db_path: str = "adk_platform.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tools table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tools (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        tool_type TEXT NOT NULL,
                        function_code TEXT,
                        parameters TEXT,
                        builtin_name TEXT,
                        external_config TEXT,
                        tags TEXT,
                        is_enabled BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create agents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agents (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        agent_type TEXT NOT NULL,
                        system_prompt TEXT,
                        instructions TEXT,
                        sub_agents TEXT,
                        tools TEXT,
                        model_settings TEXT,
                        workflow_config TEXT,
                        ui_config TEXT,
                        tags TEXT,
                        version TEXT DEFAULT '1.0.0',
                        is_enabled BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create projects table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        agents TEXT,
                        tools TEXT,
                        config TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create chat_sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        user_id TEXT,
                        messages TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (agent_id) REFERENCES agents (id)
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string"""
        if data is None:
            return None
        return json.dumps(data, default=str)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data"""
        if data is None:
            return None
        try:
            return json.loads(data)
        except:
            return data
    
    # Tool Management
    def save_tool(self, tool_data: Dict[str, Any]) -> bool:
        """Save or update a tool"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if tool exists
                cursor.execute("SELECT id FROM tools WHERE id = ?", (tool_data['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing tool
                    cursor.execute('''
                        UPDATE tools SET
                            name = ?, description = ?, tool_type = ?, function_code = ?,
                            parameters = ?, builtin_name = ?, external_config = ?, tags = ?,
                            is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        tool_data['name'],
                        tool_data['description'],
                        tool_data['tool_type'],
                        tool_data.get('function_code'),
                        self._serialize_json(tool_data.get('parameters')),
                        tool_data.get('builtin_name'),
                        self._serialize_json(tool_data.get('external_config')),
                        self._serialize_json(tool_data.get('tags')),
                        tool_data.get('is_enabled', True),
                        tool_data['id']
                    ))
                else:
                    # Insert new tool
                    cursor.execute('''
                        INSERT INTO tools (
                            id, name, description, tool_type, function_code,
                            parameters, builtin_name, external_config, tags, is_enabled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tool_data['id'],
                        tool_data['name'],
                        tool_data['description'],
                        tool_data['tool_type'],
                        tool_data.get('function_code'),
                        self._serialize_json(tool_data.get('parameters')),
                        tool_data.get('builtin_name'),
                        self._serialize_json(tool_data.get('external_config')),
                        self._serialize_json(tool_data.get('tags')),
                        tool_data.get('is_enabled', True)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving tool: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tools WHERE id = ?", (tool_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    tool_data = dict(zip(columns, row))
                    
                    # Deserialize JSON fields
                    tool_data['parameters'] = self._deserialize_json(tool_data['parameters'])
                    tool_data['external_config'] = self._deserialize_json(tool_data['external_config'])
                    tool_data['tags'] = self._deserialize_json(tool_data['tags'])
                    
                    return tool_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tool: {e}")
            return None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tools WHERE is_enabled = 1 ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                tools = []
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    tool_data = dict(zip(columns, row))
                    tool_data['parameters'] = self._deserialize_json(tool_data['parameters'])
                    tool_data['external_config'] = self._deserialize_json(tool_data['external_config'])
                    tool_data['tags'] = self._deserialize_json(tool_data['tags'])
                    tools.append(tool_data)
                
                return tools
                
        except Exception as e:
            logger.error(f"Error getting all tools: {e}")
            return []
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool (soft delete by setting is_enabled to False)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tools SET is_enabled = 0 WHERE id = ?", (tool_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            return False
    
    # Agent Management
    def save_agent(self, agent_data: Dict[str, Any]) -> bool:
        """Save or update an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if agent exists
                cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_data['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing agent
                    cursor.execute('''
                        UPDATE agents SET
                            name = ?, description = ?, agent_type = ?, system_prompt = ?,
                            instructions = ?, sub_agents = ?, tools = ?, model_settings = ?,
                            workflow_config = ?, ui_config = ?, tags = ?, version = ?,
                            is_enabled = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        agent_data['name'],
                        agent_data['description'],
                        agent_data['agent_type'],
                        agent_data.get('system_prompt'),
                        agent_data.get('instructions'),
                        self._serialize_json(agent_data.get('sub_agents')),
                        self._serialize_json(agent_data.get('tools')),
                        self._serialize_json(agent_data.get('model_settings')),
                        self._serialize_json(agent_data.get('workflow_config')),
                        self._serialize_json(agent_data.get('ui_config')),
                        self._serialize_json(agent_data.get('tags')),
                        agent_data.get('version', '1.0.0'),
                        agent_data.get('is_enabled', True),
                        agent_data['id']
                    ))
                else:
                    # Insert new agent
                    cursor.execute('''
                        INSERT INTO agents (
                            id, name, description, agent_type, system_prompt,
                            instructions, sub_agents, tools, model_settings,
                            workflow_config, ui_config, tags, version, is_enabled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        agent_data['id'],
                        agent_data['name'],
                        agent_data['description'],
                        agent_data['agent_type'],
                        agent_data.get('system_prompt'),
                        agent_data.get('instructions'),
                        self._serialize_json(agent_data.get('sub_agents')),
                        self._serialize_json(agent_data.get('tools')),
                        self._serialize_json(agent_data.get('model_settings')),
                        self._serialize_json(agent_data.get('workflow_config')),
                        self._serialize_json(agent_data.get('ui_config')),
                        self._serialize_json(agent_data.get('tags')),
                        agent_data.get('version', '1.0.0'),
                        agent_data.get('is_enabled', True)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving agent: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    agent_data = dict(zip(columns, row))
                    
                    # Deserialize JSON fields
                    agent_data['sub_agents'] = self._deserialize_json(agent_data['sub_agents'])
                    agent_data['tools'] = self._deserialize_json(agent_data['tools'])
                    agent_data['model_settings'] = self._deserialize_json(agent_data['model_settings'])
                    agent_data['workflow_config'] = self._deserialize_json(agent_data['workflow_config'])
                    agent_data['ui_config'] = self._deserialize_json(agent_data['ui_config'])
                    agent_data['tags'] = self._deserialize_json(agent_data['tags'])
                    
                    return agent_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
            return None
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE is_enabled = 1 ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                agents = []
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    agent_data = dict(zip(columns, row))
                    agent_data['sub_agents'] = self._deserialize_json(agent_data['sub_agents'])
                    agent_data['tools'] = self._deserialize_json(agent_data['tools'])
                    agent_data['model_settings'] = self._deserialize_json(agent_data['model_settings'])
                    agent_data['workflow_config'] = self._deserialize_json(agent_data['workflow_config'])
                    agent_data['ui_config'] = self._serialize_json(agent_data['ui_config'])
                    agent_data['tags'] = self._deserialize_json(agent_data['tags'])
                    agents.append(agent_data)
                
                return agents
                
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            return []
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent (soft delete)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE agents SET is_enabled = 0 WHERE id = ?", (agent_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False
    
    # Project Management
    def save_project(self, project_data: Dict[str, Any]) -> bool:
        """Save or update a project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if project exists
                cursor.execute("SELECT id FROM projects WHERE id = ?", (project_data['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing project
                    cursor.execute('''
                        UPDATE projects SET
                            name = ?, description = ?, agents = ?, tools = ?, config = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        project_data['name'],
                        project_data['description'],
                        self._serialize_json(project_data.get('agents')),
                        self._serialize_json(project_data.get('tools')),
                        self._serialize_json(project_data.get('config')),
                        project_data['id']
                    ))
                else:
                    # Insert new project
                    cursor.execute('''
                        INSERT INTO projects (
                            id, name, description, agents, tools, config
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        project_data['id'],
                        project_data['name'],
                        project_data['description'],
                        self._serialize_json(project_data.get('agents')),
                        self._serialize_json(project_data.get('tools')),
                        self._serialize_json(project_data.get('config'))
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return False
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                projects = []
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    project_data = dict(zip(columns, row))
                    project_data['agents'] = self._deserialize_json(project_data['agents'])
                    project_data['tools'] = self._deserialize_json(project_data['tools'])
                    project_data['config'] = self._deserialize_json(project_data['config'])
                    projects.append(project_data)
                
                return projects
                
        except Exception as e:
            logger.error(f"Error getting all projects: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    project_data = dict(zip(columns, row))
                    
                    # Deserialize JSON fields
                    project_data['agents'] = self._deserialize_json(project_data['agents'])
                    project_data['tools'] = self._deserialize_json(project_data['tools'])
                    project_data['config'] = self._deserialize_json(project_data['config'])
                    
                    return project_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    # Chat Session Management
    def save_chat_session(self, session_data: Dict[str, Any]) -> bool:
        """Save or update a chat session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if session exists
                cursor.execute("SELECT id FROM chat_sessions WHERE id = ?", (session_data['id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing session
                    cursor.execute('''
                        UPDATE chat_sessions SET
                            messages = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        self._serialize_json(session_data.get('messages')),
                        session_data['id']
                    ))
                else:
                    # Insert new session
                    cursor.execute('''
                        INSERT INTO chat_sessions (
                            id, agent_id, user_id, messages
                        ) VALUES (?, ?, ?, ?)
                    ''', (
                        session_data['id'],
                        session_data['agent_id'],
                        session_data.get('user_id'),
                        self._serialize_json(session_data.get('messages'))
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving chat session: {e}")
            return False
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    session_data = dict(zip(columns, row))
                    session_data['messages'] = self._deserialize_json(session_data['messages'])
                    return session_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    def get_chat_sessions_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chat_sessions WHERE agent_id = ? ORDER BY updated_at DESC", (agent_id,))
                rows = cursor.fetchall()
                
                sessions = []
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    session_data = dict(zip(columns, row))
                    session_data['messages'] = self._deserialize_json(session_data['messages'])
                    sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Error getting chat sessions by agent: {e}")
            return []
    
    def close(self):
        """Close database connections"""
        pass  # SQLite handles this automatically
