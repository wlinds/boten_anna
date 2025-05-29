import re
from datetime import datetime, timedelta
from services.reputation_service import reputation_service

class BehaviorAnalyzer:
    """Analyzes user messages and updates reputation accordingly"""
    
    def __init__(self):
        # TODO Improve this?
        self.politeness_words = ['tack', 'snälla', 'please', 'thanks', 'sorry', 'ursäkta']
        self.rudeness_words = ['stupid', 'dum', 'idiot', 'fan', 'skit', 'bög']
        self.humor_indicators = ['😂', '🤣', 'lol', 'haha', 'lmao', 'rofl']
        self.question_patterns = ['?', 'hur', 'vad', 'när', 'varför', 'how', 'what', 'when', 'why']
    
    def analyze_message(self, user_id: str, message: str, context: dict = None):
        """Analyze a message and update reputation"""
        context = context or {}
        
        # Basic engagement
        reputation_service.update_trait(user_id, 'engagement', 0.1, 'Sent message')
        
        # Analyze politeness
        polite_words = sum(1 for word in self.politeness_words if word in message.lower())
        rude_words = sum(1 for word in self.rudeness_words if word in message.lower())
        
        if polite_words > 0:
            reputation_service.update_trait(user_id, 'politeness', polite_words * 0.5, 'Used polite language')
        if rude_words > 0:
            reputation_service.update_trait(user_id, 'politeness', -rude_words * 1.0, 'Used rude language')
            reputation_service.update_trait(user_id, 'respect', -rude_words * 0.5, 'Disrespectful language')
        
        # Analyze humor
        humor_score = sum(1 for indicator in self.humor_indicators if indicator in message)
        if humor_score > 0:
            reputation_service.update_trait(user_id, 'humor', humor_score * 0.3, 'Showed humor')
        
        # Check if asking questions (shows engagement)
        if any(pattern in message.lower() for pattern in self.question_patterns):
            reputation_service.update_trait(user_id, 'engagement', 0.2, 'Asked question')
        
        # Check message length (spam detection)
        if len(message) > 200:
            reputation_service.update_trait(user_id, 'spam_tendency', 0.3, 'Very long message')
        elif len(message) < 5:
            reputation_service.update_trait(user_id, 'spam_tendency', 0.1, 'Very short message')
        
        # Check for caps (shouting)
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.5 and len(message) > 10:
            reputation_service.update_trait(user_id, 'chaos_factor', 0.5, 'Excessive caps')
            reputation_service.update_trait(user_id, 'politeness', -0.3, 'Shouting')
    
    def analyze_spam_behavior(self, user_id: str, message_count: int, timeframe_seconds: int):
        """Analyze spam behavior"""
        if message_count >= 5 and timeframe_seconds <= 30:
            spam_score = (message_count - 4) * 0.8
            reputation_service.update_trait(user_id, 'spam_tendency', spam_score, f'Sent {message_count} messages in {timeframe_seconds}s')
            reputation_service.update_trait(user_id, 'respect', -spam_score * 0.3, 'Spamming behavior')
    
    def analyze_response_to_anna(self, user_id: str, message: str, was_positive: bool):
        """Analyze how user responds to Anna"""
        if was_positive:
            reputation_service.update_trait(user_id, 'respect', 0.5, 'Positive response to Anna')
            reputation_service.update_trait(user_id, 'engagement', 0.3, 'Engaged positively')
        else:
            reputation_service.update_trait(user_id, 'respect', -0.3, 'Negative response to Anna')
    
    def analyze_helpfulness(self, user_id: str, helped_someone: bool):
        """Track when users help others"""
        if helped_someone:
            reputation_service.update_trait(user_id, 'helpfulness', 1.0, 'Helped another user')
            reputation_service.update_trait(user_id, 'respect', 0.2, 'Showed community spirit')

# Singleton instance
behavior_analyzer = BehaviorAnalyzer()