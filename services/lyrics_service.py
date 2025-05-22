import os
import random
from typing import List, Dict

class LyricsService:
    """Service for accessing and retrieving lyrics"""
    
    def __init__(self):
        self.lyrics_path = os.path.join(os.path.dirname(__file__), '../data/lyrics.txt')

        # Keywords to help categorize lines for different situations
        self.kick_keywords = ['banna', 'kicka', 'röjer upp', 'spammar', 'gör sig av', 'slår']
        self.greeting_keywords = ['känner en bot', 'heter Anna', 'vaktar']
        self.bot_identity_keywords = ['känner en bot', 'hon heter Anna', 'Anna heter hon']

        self.lyrics = self._load_lyrics()
        self.sections = self._parse_sections()
        
    
    def _load_lyrics(self) -> List[str]:
        try:
            with open(self.lyrics_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading lyrics: {e}")
            return []
    
    def _parse_sections(self) -> Dict[str, List[str]]:
        """Parse lyrics into sections (verse, chorus, etc.)"""
        sections = {
            'chorus': [],
            'verse': [],
            'kick': [],         # Lines about kicking/banning
            'greeting': [],     # Lines good for greetings
            'identity': []      # Lines about Anna's identity
        }
        
        current_section = 'chorus'  # Default to chorus
        
        for line in self.lyrics:
            # Check for section headers
            if line.startswith('[Chorus'):
                current_section = 'chorus'
                continue
            elif line.startswith('[Verse'):
                current_section = 'verse'
                continue
            
            # Add line to appropriate section
            sections[current_section].append(line)
            
            # Also categorize by content
            for keyword in self.kick_keywords:
                if keyword in line.lower():
                    sections['kick'].append(line)
                    break
                    
            for keyword in self.greeting_keywords:
                if keyword in line.lower():
                    sections['greeting'].append(line)
                    break
                    
            for keyword in self.bot_identity_keywords:
                if keyword in line.lower():
                    sections['identity'].append(line)
                    break
        
        return sections
    
    def get_random_line(self, section: str = None) -> str:
        """Get a random line from the specified section"""
        if not section or section not in self.sections or not self.sections[section]:
            # Default to any line if section is not specified or empty
            return random.choice(self.lyrics) if self.lyrics else "Jag känner en bot!"
        
        return random.choice(self.sections[section])
    
    def get_kick_line(self) -> str:
        """Get a random line appropriate for kicking users"""
        return self.get_random_line('kick')
    
    def get_greeting_line(self) -> str:
        """Get a random line appropriate for greetings"""
        return self.get_random_line('greeting')
    
    def get_identity_line(self) -> str:
        """Get a random line about Anna's identity"""
        return self.get_random_line('identity')

lyrics_service = LyricsService() # Singleton instance