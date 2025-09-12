"""
Firestore database manager for the Google ADK No-Code Platform
Replaces SQLite with Google Cloud Firestore for production deployment
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Import Firestore
try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    FIRESTORE_AVAILABLE = True
    print("Google Cloud Firestore loaded successfully")
except ImportError as e:
    FIRESTORE_AVAILABLE = False
    print(f"Warning: Google Cloud Firestore not available. Import error: {e}")
    print("Install with: pip install google-cloud-firestore")

logger = logging.getLogger(__name__)

class FirestoreManager:
    """Firestore database manager for storing agents, tools, and projects"""
    
    def __init__(self, service_account_path: str = "svcacct.json", project_id: str = "tsl-generative-ai"):
        self.project_id = project_id
        self.collection_name = "agent-genie"
        self.db = None
        self.collection = None
        
        if not FIRESTORE_AVAILABLE:
            raise ImportError("Google Cloud Firestore is not available. Please install google-cloud-firestore")
        
        self._initialize_firestore(service_account_path)
    
    def _initialize_firestore(self, service_account_path: str):
        """Initialize Firestore client with service account"""
        try:
            # Check if service account file exists
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Initialize Firestore client
            self.db = firestore.Client(
                project=self.project_id,
                credentials=credentials
            )
            
            # Get reference to the main collection
            self.collection = self.db.collection(self.collection_name)
            
            logger.info(f"Firestore initialized successfully for project: {self.project_id}")
            logger.info(f"Using collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Firestore: {e}")
            raise
    
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for Firestore storage"""
        if data is None:
            return None
        
        # Convert datetime objects to ISO strings
        if isinstance(data, datetime):
            return data.isoformat()
        
        # Handle lists and dicts recursively
        if isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        
        if isinstance(data, dict):
            return {key: self._serialize_data(value) for key, value in data.items()}
        
        # Return primitive types as-is
        return data
    
    def _deserialize_data(self, data: Any) -> Any:
        """Deserialize data from Firestore storage"""
        if data is None:
            return None
        
        # Handle lists and dicts recursively
        if isinstance(data, (list, tuple)):
            return [self._deserialize_data(item) for item in data]
        
        if isinstance(data, dict):
            return {key: self._deserialize_data(value) for key, value in data.items()}
        
        # Return primitive types as-is
        return data
    
    # Tool Management
    def save_tool(self, tool_data: Dict[str, Any]) -> bool:
        """Save or update a tool"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(tool_data)
            
            # Add/update timestamp
            serialized_data['updated_at'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('tools').collection('items').document(tool_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Tool {tool_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tool: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a tool by ID"""
        try:
            doc_ref = self.collection.document('tools').collection('items').document(tool_id)
            doc = doc_ref.get()
            
            if doc.exists:
                tool_data = doc.to_dict()
                return self._deserialize_data(tool_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting tool: {e}")
            return None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all tools"""
        try:
            tools_ref = self.collection.document('tools').collection('items')
            docs = tools_ref.where('is_enabled', '==', True).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
            tools = []
            for doc in docs:
                tool_data = doc.to_dict()
                tool_data['id'] = doc.id  # Ensure ID is included
                tools.append(self._deserialize_data(tool_data))
            
            return tools
            
        except Exception as e:
            logger.error(f"Error getting all tools: {e}")
            return []
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool (soft delete by setting is_enabled to False)"""
        try:
            doc_ref = self.collection.document('tools').collection('items').document(tool_id)
            doc_ref.update({
                'is_enabled': False,
                'updated_at': datetime.now().isoformat()
            })
            
            logger.info(f"Tool {tool_id} soft deleted from Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            return False
    
    # Agent Management
    def save_agent(self, agent_data: Dict[str, Any]) -> bool:
        """Save or update an agent"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(agent_data)
            
            # Add/update timestamp
            serialized_data['updated_at'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('agents').collection('items').document(agent_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Agent {agent_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving agent: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID"""
        try:
            doc_ref = self.collection.document('agents').collection('items').document(agent_id)
            doc = doc_ref.get()
            
            if doc.exists:
                agent_data = doc.to_dict()
                agent_data['id'] = doc.id  # Ensure ID is included
                return self._deserialize_data(agent_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
            return None
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            agents_ref = self.collection.document('agents').collection('items')
            docs = agents_ref.where('is_enabled', '==', True).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
            agents = []
            for doc in docs:
                try:
                    agent_data = doc.to_dict()
                    agent_data['id'] = doc.id  # Ensure ID is included
                    
                    # Safely deserialize JSON fields with error handling
                    try:
                        agent_data['sub_agents'] = self._deserialize_data(agent_data.get('sub_agents'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize sub_agents for agent {doc.id}: {e}")
                        agent_data['sub_agents'] = []
                    
                    try:
                        agent_data['tools'] = self._deserialize_data(agent_data.get('tools'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize tools for agent {doc.id}: {e}")
                        agent_data['tools'] = []
                    
                    try:
                        agent_data['model_settings'] = self._deserialize_data(agent_data.get('model_settings'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize model_settings for agent {doc.id}: {e}")
                        agent_data['model_settings'] = {}
                    
                    try:
                        agent_data['workflow_config'] = self._deserialize_data(agent_data.get('workflow_config'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize workflow_config for agent {doc.id}: {e}")
                        agent_data['workflow_config'] = {}
                    
                    try:
                        agent_data['ui_config'] = self._deserialize_data(agent_data.get('ui_config'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize ui_config for agent {doc.id}: {e}")
                        agent_data['ui_config'] = {}
                    
                    try:
                        agent_data['tags'] = self._deserialize_data(agent_data.get('tags'))
                    except Exception as e:
                        logger.warning(f"Failed to deserialize tags for agent {doc.id}: {e}")
                        agent_data['tags'] = []
                    
                    agents.append(agent_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process agent row: {e}, doc_id: {doc.id}")
                    continue
            
            return agents
            
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            return []
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent (soft delete)"""
        try:
            doc_ref = self.collection.document('agents').collection('items').document(agent_id)
            doc_ref.update({
                'is_enabled': False,
                'updated_at': datetime.now().isoformat()
            })
            
            logger.info(f"Agent {agent_id} soft deleted from Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False
    
    # Project Management
    def save_project(self, project_data: Dict[str, Any]) -> bool:
        """Save or update a project"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(project_data)
            
            # Add/update timestamp
            serialized_data['updated_at'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('projects').collection('items').document(project_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Project {project_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return False
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        try:
            projects_ref = self.collection.document('projects').collection('items')
            docs = projects_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
            projects = []
            for doc in docs:
                project_data = doc.to_dict()
                project_data['id'] = doc.id  # Ensure ID is included
                
                # Deserialize JSON fields
                project_data['agents'] = self._deserialize_data(project_data.get('agents'))
                project_data['tools'] = self._deserialize_data(project_data.get('tools'))
                project_data['config'] = self._deserialize_data(project_data.get('config'))
                
                projects.append(project_data)
            
            return projects
            
        except Exception as e:
            logger.error(f"Error getting all projects: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID"""
        try:
            doc_ref = self.collection.document('projects').collection('items').document(project_id)
            doc = doc_ref.get()
            
            if doc.exists:
                project_data = doc.to_dict()
                project_data['id'] = doc.id  # Ensure ID is included
                
                # Deserialize JSON fields
                project_data['agents'] = self._deserialize_data(project_data.get('agents'))
                project_data['tools'] = self._deserialize_data(project_data.get('tools'))
                project_data['config'] = self._deserialize_data(project_data.get('config'))
                
                return project_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID"""
        try:
            doc_ref = self.collection.document('projects').collection('items').document(project_id)
            doc_ref.delete()
            
            logger.info(f"Project {project_id} deleted from Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False
    
    # Chat Session Management
    def save_chat_session(self, session_data: Dict[str, Any]) -> bool:
        """Save or update a chat session"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(session_data)
            
            # Add/update timestamp
            serialized_data['updated_at'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('chat_sessions').collection('items').document(session_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Chat session {session_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chat session: {e}")
            return False
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat session by ID"""
        try:
            doc_ref = self.collection.document('chat_sessions').collection('items').document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                session_data = doc.to_dict()
                session_data['id'] = doc.id  # Ensure ID is included
                session_data['messages'] = self._deserialize_data(session_data.get('messages'))
                return session_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    def get_chat_sessions_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for an agent"""
        try:
            sessions_ref = self.collection.document('chat_sessions').collection('items')
            docs = sessions_ref.where('agent_id', '==', agent_id).order_by('updated_at', direction=firestore.Query.DESCENDING).stream()
            
            sessions = []
            for doc in docs:
                session_data = doc.to_dict()
                session_data['id'] = doc.id  # Ensure ID is included
                session_data['messages'] = self._deserialize_data(session_data.get('messages'))
                sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting chat sessions by agent: {e}")
            return []
    
    # User Management
    def save_user(self, user_data: Dict[str, Any]) -> bool:
        """Save or update a user"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(user_data)
            
            # Add/update timestamp
            serialized_data['updated_at'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('users').collection('items').document(user_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"User {user_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email"""
        try:
            users_ref = self.collection.document('users').collection('items')
            docs = users_ref.where('email', '==', email).where('is_active', '==', True).limit(1).stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id  # Ensure ID is included
                user_data['metadata'] = self._deserialize_data(user_data.get('metadata'))
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        try:
            doc_ref = self.collection.document('users').collection('items').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                user_data['id'] = doc.id  # Ensure ID is included
                user_data['metadata'] = self._deserialize_data(user_data.get('metadata'))
                return user_data
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    # Session Management
    def save_user_session(self, session_data: Dict[str, Any]) -> bool:
        """Save or update a user session"""
        try:
            # Serialize data for Firestore
            serialized_data = self._serialize_data(session_data)
            
            # Add/update timestamp
            serialized_data['last_activity'] = datetime.now().isoformat()
            
            # Save to Firestore
            doc_ref = self.collection.document('user_sessions').collection('items').document(session_data['id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"User session {session_data['id']} saved to Firestore")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user session: {e}")
            return False
    
    def get_user_session_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get a user session by token"""
        try:
            sessions_ref = self.collection.document('user_sessions').collection('items')
            docs = sessions_ref.where('session_token', '==', session_token).limit(1).stream()
            
            for doc in docs:
                session_data = doc.to_dict()
                session_data['id'] = doc.id  # Ensure ID is included
                
                # Check if session is expired
                expires_at = session_data.get('expires_at')
                if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                    # Session expired, delete it
                    self.delete_user_session(session_token)
                    return None
                
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user session by token: {e}")
            return None
    
    def delete_user_session(self, session_token: str) -> bool:
        """Delete a user session"""
        try:
            sessions_ref = self.collection.document('user_sessions').collection('items')
            docs = sessions_ref.where('session_token', '==', session_token).stream()
            
            for doc in docs:
                doc.reference.delete()
                logger.info(f"User session {session_token} deleted from Firestore")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user session: {e}")
            return False
    
    def close(self):
        """Close Firestore connections"""
        # Firestore client handles connection cleanup automatically
        pass
    
    def initialize_collections(self):
        """Initialize the Firestore collection structure"""
        try:
            # Create the main collection structure
            collections = ['tools', 'agents', 'projects', 'chat_sessions', 'users', 'user_sessions']
            
            for collection_name in collections:
                # Create a subcollection for each main collection
                subcollection_ref = self.collection.document(collection_name).collection('items')
                
                # Add a placeholder document to ensure the collection exists
                placeholder_doc = subcollection_ref.document('_placeholder')
                placeholder_doc.set({
                    'created_at': datetime.now().isoformat(),
                    'placeholder': True,
                    'description': f'Placeholder document for {collection_name} collection'
                })
                
                # Delete the placeholder document
                placeholder_doc.delete()
                
                logger.info(f"Initialized collection: {collection_name}")
            
            logger.info("Firestore collection structure initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            raise
    
    def save_agent_embed(self, embed_data: Dict[str, Any]) -> bool:
        """Save agent embed configuration to Firestore"""
        try:
            embed_id = embed_data.get('embed_id')
            if not embed_id:
                logger.error("Embed ID is required")
                return False
            
            # Store in agent_embeds subcollection
            embed_ref = self.collection.document('agent_embeds').collection('items').document(embed_id)
            embed_ref.set(embed_data)
            
            logger.info(f"Saved agent embed: {embed_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving agent embed: {e}")
            return False
    
    def get_agent_embed(self, embed_id: str) -> Optional[Dict[str, Any]]:
        """Get agent embed configuration from Firestore"""
        try:
            embed_ref = self.collection.document('agent_embeds').collection('items').document(embed_id)
            doc = embed_ref.get()
            
            if doc.exists:
                embed_data = doc.to_dict()
                embed_data['id'] = doc.id
                return embed_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting agent embed: {e}")
            return None
    
    def get_agent_embeds(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all embeds for an agent from Firestore"""
        try:
            embeds_ref = self.collection.document('agent_embeds').collection('items')
            docs = embeds_ref.where('agent_id', '==', agent_id).order_by('created_at', direction='DESCENDING').stream()
            
            embeds = []
            for doc in docs:
                embed_data = doc.to_dict()
                embed_data['id'] = doc.id
                embeds.append(embed_data)
            
            return embeds
            
        except Exception as e:
            logger.error(f"Error getting agent embeds: {e}")
            return []
    
    def update_embed_access(self, embed_id: str) -> bool:
        """Update embed access statistics in Firestore"""
        try:
            embed_ref = self.collection.document('agent_embeds').collection('items').document(embed_id)
            
            # Use Firestore transaction for atomic update
            @firestore.transactional
            def update_access(transaction):
                doc = embed_ref.get(transaction=transaction)
                if doc.exists:
                    current_data = doc.to_dict()
                    access_count = current_data.get('access_count', 0) + 1
                    
                    transaction.update(embed_ref, {
                        'access_count': access_count,
                        'last_accessed': datetime.now().isoformat()
                    })
                    return True
                return False
            
            # Create transaction and execute
            transaction = self.db.transaction()
            return update_access(transaction)
            
        except Exception as e:
            logger.error(f"Error updating embed access: {e}")
            return False
    
    def delete_agent_embed(self, embed_id: str) -> bool:
        """Delete an agent embed from Firestore"""
        try:
            embed_ref = self.collection.document('agent_embeds').collection('items').document(embed_id)
            embed_ref.delete()
            
            logger.info(f"Deleted agent embed: {embed_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting agent embed: {e}")
            return False
    
    def get_all_chat_sessions(self) -> List[Dict[str, Any]]:
        """Get all chat sessions from Firestore"""
        try:
            sessions_ref = self.collection.document('chat_sessions').collection('items')
            docs = sessions_ref.stream()
            
            sessions = []
            for doc in docs:
                session_data = doc.to_dict()
                session_data['id'] = doc.id
                sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting all chat sessions: {e}")
            return []
