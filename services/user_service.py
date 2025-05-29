import json
import os
from typing import Dict, Optional, List
from telegram import Update, User
from datetime import datetime

class UserService:
    """Service for managing user information"""
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), '../data/users.json')
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Dict]:
        """Load users from file"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                return {}
        return {}
    
    def _save_users(self):
        """Save users to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def update_user(self, user: User) -> None:
        """Update user information"""
        user_id = str(user.id)
        current_time = datetime.now().isoformat()
        
        # Create or update user record
        if user_id not in self.users:
            self.users[user_id] = {
                'first_seen': current_time,
                'message_count': 0
            }
        
        # Update user info
        self.users[user_id].update({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'last_seen': current_time,
            'is_bot': user.is_bot,
            'language_code': user.language_code
        })
        
        # Increment message count
        self.users[user_id]['message_count'] = self.users[user_id].get('message_count', 0) + 1
        
        # Save periodically (every 10 updates)
        if self.users[user_id]['message_count'] % 10 == 0:
            self._save_users()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user information by ID"""
        return self.users.get(user_id)
    
    def get_user_display_name(self, user_id: str) -> str:
        """Get the best display name for a user"""
        user = self.get_user(user_id)
        if not user:
            return f"User {user_id}"
        
        # Priority: first_name, username, user_id
        if user.get('first_name'):
            return user['first_name']
        elif user.get('username'):
            return f"@{user['username']}"
        else:
            return f"User {user_id}"
    
    def get_all_users(self) -> Dict[str, Dict]:
        """Get all users"""
        return self.users.copy()
    
    def get_active_users(self, days: int = 30) -> Dict[str, Dict]:
        """Get users active in the last N days"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        active_users = {}
        for user_id, user_data in self.users.items():
            if user_data.get('last_seen'):
                try:
                    last_seen = datetime.fromisoformat(user_data['last_seen'])
                    if last_seen > cutoff:
                        active_users[user_id] = user_data
                except:
                    pass
        
        return active_users
    
    def search_users(self, query: str) -> List[Dict]:
        """Search users by name or username"""
        query = query.lower()
        matches = []
        
        for user_id, user_data in self.users.items():
            # Search in first name, last name, and username
            searchable_fields = [
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('username', '')
            ]
            
            if any(query in field.lower() for field in searchable_fields if field):
                matches.append({**user_data, 'user_id': user_id})
        
        return matches

user_service = UserService()