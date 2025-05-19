import os
import json
from typing import Dict, List, Any

class ChatStore:
    """
    Handles storing and retrieving chat data
    """
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), 'chat_histories.json')
        self.list_data_path = os.path.join(os.path.dirname(__file__), 'chat_lists.json')
        self.chat_lists = self._load_chat_lists()
    
    def _load_chat_lists(self) -> Dict[str, List[str]]:
        """Load chat lists from file or initialize empty dict"""
        if os.path.exists(self.list_data_path):
            try:
                with open(self.list_data_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading chat lists: {e}")
                return {}
        return {}
    
    def save_chat_lists(self, chat_lists: Dict[str, List[str]]) -> None:
        """Save chat lists to file"""
        try:
            with open(self.list_data_path, 'w') as f:
                json.dump(chat_lists, f, indent=2)
        except Exception as e:
            print(f"Error saving chat lists: {e}")
    
    def get_chat_list(self, chat_id: str) -> List[str]:
        """Get the list for a specific chat"""
        if chat_id not in self.chat_lists:
            self.chat_lists[chat_id] = []
        return self.chat_lists[chat_id]
    
    def add_item_to_list(self, chat_id: str, item: str) -> None:
        """Add an item to a chat's list"""
        if chat_id not in self.chat_lists:
            self.chat_lists[chat_id] = []
        
        self.chat_lists[chat_id].append(item)
        self.save_chat_lists(self.chat_lists)
    
    def remove_item_from_list(self, chat_id: str, item: str) -> bool:
        """Remove an item from a chat's list. Returns True if item was found and removed."""
        if chat_id not in self.chat_lists:
            return False
        
        if item in self.chat_lists[chat_id]:
            self.chat_lists[chat_id].remove(item)
            self.save_chat_lists(self.chat_lists)
            return True
        
        return False
    
    def clear_list(self, chat_id: str) -> None:
        """Clear a chat's list"""
        if chat_id in self.chat_lists:
            self.chat_lists[chat_id] = []
            self.save_chat_lists(self.chat_lists)

# Singleton instance
chat_store = ChatStore()