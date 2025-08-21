"""
Authentication service for the Google ADK No-Code Platform
"""

import uuid
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .models import User, UserSession, LoginRequest, RegisterRequest, AuthResponse
from .database import DatabaseManager


class AuthService:
    """Service for handling user authentication and session management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session_duration = 24 * 60 * 60  # 24 hours in seconds
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return self._hash_password(password) == hashed
    
    def _generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def _create_user_session(self, user_id: str, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> UserSession:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        session_token = self._generate_session_token()
        expires_at = (datetime.now() + timedelta(seconds=self.session_duration)).isoformat()
        
        session = UserSession(
            id=session_id,
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Save session to database
        session_data = session.model_dump()
        if self.db_manager.save_user_session(session_data):
            return session
        else:
            raise Exception("Failed to save user session")
    
    def register_user(self, request: RegisterRequest) -> AuthResponse:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = self.db_manager.get_user_by_email(request.email)
            if existing_user:
                return AuthResponse(
                    success=False,
                    message="User with this email already exists"
                )
            
            # Create new user
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(request.password)
            
            user = User(
                id=user_id,
                email=request.email,
                name=request.name,
                password_hash=password_hash
            )
            
            # Save user to database
            user_data = user.model_dump()
            if self.db_manager.save_user(user_data):
                return AuthResponse(
                    success=True,
                    user=user,
                    message="User registered successfully"
                )
            else:
                return AuthResponse(
                    success=False,
                    message="Failed to save user"
                )
                
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"Registration failed: {str(e)}"
            )
    
    def login_user(self, request: LoginRequest, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> AuthResponse:
        """Authenticate a user and create a session"""
        try:
            # Get user by email
            user_data = self.db_manager.get_user_by_email(request.email)
            if not user_data:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Verify password
            if not self._verify_password(request.password, user_data['password_hash']):
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Check if user is active
            if not user_data.get('is_active', True):
                return AuthResponse(
                    success=False,
                    message="User account is deactivated"
                )
            
            # Create user object
            user = User(**user_data)
            
            # Update last login
            user.last_login = datetime.now().isoformat()
            user_data = user.model_dump()
            self.db_manager.save_user(user_data)
            
            # Create session
            session = self._create_user_session(user.id, user_agent, ip_address)
            
            return AuthResponse(
                success=True,
                user=user,
                session_token=session.session_token,
                message="Login successful"
            )
            
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Validate a session token and return the associated user"""
        try:
            session_data = self.db_manager.get_user_session_by_token(session_token)
            if not session_data:
                return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                # Session expired, delete it
                self.db_manager.delete_user_session(session_token)
                return None
            
            # Get user data
            user_data = self.db_manager.get_user_by_id(session_data['user_id'])
            if not user_data:
                return None
            
            # Update session activity
            self.db_manager.save_user_session(session_data)
            
            return User(**user_data)
            
        except Exception as e:
            print(f"Error validating session: {e}")
            return None
    
    def logout_user(self, session_token: str) -> bool:
        """Logout a user by deleting their session"""
        try:
            return self.db_manager.delete_user_session(session_token)
        except Exception as e:
            print(f"Error logging out user: {e}")
            return False
    
    def get_user_by_session(self, session_token: str) -> Optional[User]:
        """Get user information from a session token"""
        return self.validate_session(session_token)

