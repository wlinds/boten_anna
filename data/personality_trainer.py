import json
import os
import time
import random
from collections import Counter
from typing import Dict, List, Any, Tuple

class PersonalityTrainer:
    """
    A class to enhance the chatbot's personality based on user interactions.
    This class analyzes chat data to build up linguistic patterns, preferences,
    and behavioral data that can be used to refine the character profile.
    """
    
    def __init__(self):
        # Define paths
        self.config_path = os.path.join(os.path.dirname(__file__), '../config/character_config.json')
        self.data_path = os.path.join(os.path.dirname(__file__), 'personality_data.json')
        
        # Load or initialize personality data
        self.personality_data = self._load_personality_data()
        # Load character config
        self.character_config = self._load_character_config()
        
        # Initialize trackers
        self.reaction_counters = self.personality_data.get('reaction_counters', {})
        self.topic_interests = self.personality_data.get('topic_interests', {})
        self.linguistic_patterns = self.personality_data.get('linguistic_patterns', {})
        self.frequent_users = self.personality_data.get('frequent_users', {})
        
    def _load_personality_data(self) -> Dict[str, Any]:
        """Load personality data from file or initialize if not exists"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading personality data: {e}")
                # Return initialized data instead of None
                return self._initialize_personality_data()
        else:
            return self._initialize_personality_data()
    
    def _initialize_personality_data(self) -> Dict[str, Any]:
        """Initialize empty personality data structure"""
        return {
            'reaction_counters': {},
            'topic_interests': {},
            'linguistic_patterns': {
                'common_phrases': [],
                'greeting_styles': [],
                'emoji_patterns': []
            },
            'frequent_users': {},
            'last_updated': int(time.time())
        }
    
    def _load_character_config(self) -> Dict[str, Any]:
        """Load character configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading character config: {e}")
            return {}
    
    def analyze_chat_history(self, chat_histories: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Analyze chat history to extract patterns
        
        Args:
            chat_histories: Dictionary of chat histories by chat_id
        """
        all_messages = []
        
        # Collect all messages from all chats
        for chat_id, messages in chat_histories.items():
            for message in messages:
                # Skip bot's own messages
                if message['role'] == 'bot':
                    continue
                
                all_messages.append(message)
                
                # Track frequent users
                user_id = message.get('user_id', 'unknown')
                if user_id not in self.frequent_users:
                    self.frequent_users[user_id] = 0
                self.frequent_users[user_id] += 1
        
        # Analyze messages for patterns if we have enough data
        if len(all_messages) >= 10:
            self._analyze_linguistic_patterns(all_messages)
            self._analyze_topic_interests(all_messages)
        
        # Update last updated timestamp
        self.personality_data['last_updated'] = int(time.time())
        
        # Save updated data
        self.save_personality_data()
    
    def _analyze_linguistic_patterns(self, messages: List[Dict[str, Any]]) -> None:
        """
        Analyze messages for linguistic patterns
        
        Args:
            messages: List of message objects
        """
        # Extract all message content
        all_text = [msg['content'] for msg in messages]
        
        # Analyze greeting patterns
        greeting_words = ['hello', 'hi', 'hey', 'hej', 'tjena', 'tja', 'hallå', 'goddag']
        greeting_patterns = []
        
        for text in all_text:
            words = text.lower().split()
            if words and words[0] in greeting_words:
                greeting_patterns.append(words[0])
        
        # Count emoji usage
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
        import re
        
        all_emojis = []
        for text in all_text:
            emojis = re.findall(emoji_pattern, text)
            all_emojis.extend(emojis)
        
        # Update linguistic patterns
        if greeting_patterns:
            counter = Counter(greeting_patterns)
            self.linguistic_patterns['greeting_styles'] = [item[0] for item in counter.most_common(5)]
        
        if all_emojis:
            counter = Counter(all_emojis)
            self.linguistic_patterns['emoji_patterns'] = [item[0] for item in counter.most_common(10)]
        
        # Update personality data
        self.personality_data['linguistic_patterns'] = self.linguistic_patterns
    
    def _analyze_topic_interests(self, messages: List[Dict[str, Any]]) -> None:
        """
        Analyze messages for topic interests
        
        Args:
            messages: List of message objects
        """
        # Define topics and their keywords
        topics = {
            'weather': ['weather', 'rain', 'sunny', 'temperature', 'forecast', 'climate'],
            'technology': ['computer', 'tech', 'app', 'software', 'hardware', 'code', 'program'],
            'food': ['food', 'eat', 'recipe', 'restaurant', 'cooking', 'lunch', 'dinner'],
            'music': ['music', 'song', 'artist', 'album', 'concert', 'playlist'],
            'movies': ['movie', 'film', 'actor', 'actress', 'cinema', 'watch'],
            'sports': ['sport', 'football', 'soccer', 'game', 'match', 'team'],
            'travel': ['travel', 'trip', 'vacation', 'holiday', 'flight', 'hotel'],
            'health': ['health', 'exercise', 'workout', 'fitness', 'doctor', 'medicine'],
            'pollen': ['pollen', 'allergy', 'allergies', 'sneeze', 'hay fever']
        }
        
        # Initialize topic counter
        topic_counter = Counter()
        
        # Count mentions of topics
        for message in messages:
            text = message['content'].lower()
            
            for topic, keywords in topics.items():
                for keyword in keywords:
                    if keyword in text:
                        topic_counter[topic] += 1
        
        # Update topic interests
        for topic, count in topic_counter.items():
            if topic not in self.topic_interests:
                self.topic_interests[topic] = 0
            self.topic_interests[topic] += count
        
        # Update personality data
        self.personality_data['topic_interests'] = self.topic_interests
    
    def track_reaction(self, reaction_type: str, message_id: str) -> None:
        """
        Track user reactions to bot messages
        
        Args:
            reaction_type: Type of reaction (like, dislike, etc.)
            message_id: ID of the message reacted to
        """
        if reaction_type not in self.reaction_counters:
            self.reaction_counters[reaction_type] = 0
        
        self.reaction_counters[reaction_type] += 1
        
        # Update personality data
        self.personality_data['reaction_counters'] = self.reaction_counters
        self.save_personality_data()
    
    def save_personality_data(self) -> None:
        """Save personality data to file"""
        try:
            with open(self.data_path, 'w') as f:
                json.dump(self.personality_data, f, indent=2)
        except Exception as e:
            print(f"Error saving personality data: {e}")
    
    def update_character_config(self) -> bool:
        """
        Update character config based on personality data
        Returns True if character config was updated, False otherwise
        """
        if not self.character_config:
            return False
        
        changed = False
        
        # Update greeting phrases if we have enough data
        if len(self.linguistic_patterns.get('greeting_styles', [])) >= 3:
            self.character_config['linguistic_profile']['speech_patterns']['common_phrases'] = list(set(
                self.character_config['linguistic_profile']['speech_patterns'].get('common_phrases', []) +
                self.linguistic_patterns.get('greeting_styles', [])
            ))
            changed = True
        
        # Update emoji usage if we have data
        emoji_count = sum(self.reaction_counters.values())
        if emoji_count > 10:
            # Determine emoji usage level
            if emoji_count > 50:
                emoji_usage = "frequent"
            elif emoji_count > 20:
                emoji_usage = "moderate"
            else:
                emoji_usage = "rare"
            
            self.character_config['linguistic_profile']['pragmatics']['emojis_usage'] = emoji_usage
            changed = True
        
        # Update topics of interest
        if self.topic_interests:
            # Find top 3 topics
            top_topics = [topic for topic, count in sorted(
                self.topic_interests.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]]
            
            if top_topics:
                if 'hobbies' not in self.character_config['behavioral_data']['lifestyle']:
                    self.character_config['behavioral_data']['lifestyle']['hobbies'] = []
                
                self.character_config['behavioral_data']['lifestyle']['hobbies'] = list(set(
                    self.character_config['behavioral_data']['lifestyle'].get('hobbies', []) +
                    top_topics
                ))
                changed = True
        
        # Save updated character config if changes were made
        if changed:
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(self.character_config, f, indent=2)
                return True
            except Exception as e:
                print(f"Error saving character config: {e}")
                return False
        
        return False
    
    def get_personality_summary(self) -> str:
        """
        Get a summary of the personality data
        
        Returns:
            str: Summary of personality data
        """
        summary = "Personality Analysis Summary:\n\n"
        
        # Add frequent users
        if self.frequent_users:
            summary += "User Interaction:\n"
            summary += f"- {len(self.frequent_users)} unique users have interacted with me\n"
            summary += f"- Most active user has sent {max(self.frequent_users.values())} messages\n\n"
        
        # Add topic interests
        if self.topic_interests:
            summary += "Topic Interests:\n"
            for topic, count in sorted(self.topic_interests.items(), key=lambda x: x[1], reverse=True)[:5]:
                summary += f"- {topic.title()}: {count} mentions\n"
            summary += "\n"
        
        # Add linguistic patterns
        if self.linguistic_patterns:
            summary += "Linguistic Patterns:\n"
            
            if self.linguistic_patterns.get('greeting_styles'):
                summary += f"- Common greetings: {', '.join(self.linguistic_patterns['greeting_styles'][:3])}\n"
            
            if self.linguistic_patterns.get('emoji_patterns'):
                summary += f"- Popular emojis: {' '.join(self.linguistic_patterns['emoji_patterns'][:5])}\n"
            
            summary += "\n"
        
        # Add last updated time
        if self.personality_data.get('last_updated'):
            last_updated = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(self.personality_data['last_updated'])
            )
            summary += f"Last updated: {last_updated}"
        
        return summary

# Singleton instance
personality_trainer = PersonalityTrainer()