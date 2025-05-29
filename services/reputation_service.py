import json
import os
import random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from services.user_service import user_service

class ReputationService:
    """Service for tracking user behavior and Anna's opinions"""
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), '../data/reputation.json')
        self.reputation_data = self._load_reputation()
        
        # Define personality traits Anna tracks
        self.traits = {
            'helpfulness': {'min': -10, 'max': 10, 'description': 'How helpful the user is'},
            'humor': {'min': -5, 'max': 15, 'description': 'How funny Anna finds them'},
            'politeness': {'min': -8, 'max': 12, 'description': 'How polite they are'},
            'spam_tendency': {'min': 0, 'max': 20, 'description': 'How spammy they are'},
            'engagement': {'min': 0, 'max': 15, 'description': 'How much they engage with Anna'},
            'respect': {'min': -10, 'max': 10, 'description': 'How much they respect Anna'},
            'chaos_factor': {'min': 0, 'max': 10, 'description': 'How much chaos they bring'}
        }
    
    def _load_reputation(self) -> Dict:
        """Load reputation data from file"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading reputation data: {e}")
                return {}
        return {}
    
    def _save_reputation(self):
        """Save reputation data to file"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.reputation_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving reputation data: {e}")
    
    def get_user_reputation(self, user_id: str) -> Dict:
        """Get user's reputation data"""
        if user_id not in self.reputation_data:
            self.reputation_data[user_id] = {
                'traits': {trait: 0 for trait in self.traits.keys()},
                'total_score': 0,
                'relationship_status': 'neutral',
                'nickname': None,
                'last_interaction': None,
                'interaction_count': 0,
                'notable_events': []
            }
        return self.reputation_data[user_id]
    
    def update_trait(self, user_id: str, trait: str, change: float, reason: str = None):
        """Update a specific trait for a user"""
        if trait not in self.traits:
            return
        
        rep = self.get_user_reputation(user_id)
        old_value = rep['traits'][trait]
        
        # Apply change with bounds
        trait_config = self.traits[trait]
        new_value = max(trait_config['min'], min(trait_config['max'], old_value + change))
        rep['traits'][trait] = new_value
        
        # Update total score (weighted average)
        rep['total_score'] = self._calculate_total_score(rep['traits'])
        rep['relationship_status'] = self._determine_relationship(rep['total_score'])
        rep['last_interaction'] = datetime.now().isoformat()
        rep['interaction_count'] += 1
        
        # Log notable events
        if abs(change) >= 2 or reason:
            rep['notable_events'].append({
                'timestamp': datetime.now().isoformat(),
                'trait': trait,
                'change': change,
                'reason': reason or 'Unknown',
                'new_value': new_value
            })
            
            # Keep only last 20 events
            rep['notable_events'] = rep['notable_events'][-20:]
        
        # Save occasionally
        if rep['interaction_count'] % 5 == 0:
            self._save_reputation()
    
    def _calculate_total_score(self, traits: Dict) -> float:
        """Calculate overall reputation score"""
        weights = {
            'helpfulness': 1.5,
            'humor': 1.2,
            'politeness': 1.3,
            'spam_tendency': -1.8,  # Negative weight
            'engagement': 1.0,
            'respect': 2.0,  # High weight
            'chaos_factor': -0.8   # Slight negative
        }
        
        weighted_sum = sum(traits[trait] * weights[trait] for trait in traits)
        return round(weighted_sum, 2)
    
    def _determine_relationship(self, total_score: float) -> str:
        """Determine relationship status based on score"""
        if total_score >= 15:
            return 'beloved'
        elif total_score >= 8:
            return 'friend'
        elif total_score >= 3:
            return 'liked'
        elif total_score >= -3:
            return 'neutral'
        elif total_score >= -8:
            return 'annoying'
        elif total_score >= -15:
            return 'disliked'
        else:
            return 'enemy'
    
    def get_opinion_about_user(self, user_id: str) -> str:
        """Get Anna's opinion about a user"""
        rep = self.get_user_reputation(user_id)
        user_name = user_service.get_user_display_name(user_id)
        relationship = rep['relationship_status']
        traits = rep['traits']
        
        opinions = {
            'beloved': [
                f"{user_name} är helt underbar! Jag älskar när hen är här i chatten 💕",
                f"ah {user_name}, min favorit! Alltid så schysst och rolig",
                f"{user_name} är typ den bästa personen här, för real!"
            ],
            'friend': [
                f"{user_name} är riktigt bra, gillar hen mycket! 😊",
                f"ah {user_name} är schysst, alltid trevlig att ha omkring",
                f"{user_name} och jag, vi hänger bra ihop!"
            ],
            'liked': [
                f"{user_name} är okej, inga problem med hen",
                f"jag gillar {user_name}, bra vibbar",
                f"{user_name} är helt chill, bra person"
            ],
            'neutral': [
                f"{user_name}? Ja, hen finns här i chatten. Det är väl okej.",
                f"hmm {user_name}... vet inte riktigt vad jag tycker än",
                f"{user_name} är där, neither good nor bad"
            ],
            'annoying': [
                f"ugh {user_name}... lite irriterande sometimes",
                f"{user_name} kan vara lite jobbig, inte gonna lie",
                f"hmm {user_name} börjar bli lite på mina nerver..."
            ],
            'disliked': [
                f"{user_name}? Nej tack. Inte min favorit direkt.",
                f"seriously {user_name}, you need to chill",
                f"{user_name} är inte så kul att ha omkring..."
            ],
            'enemy': [
                f"{user_name}... vi har problem. Jag kan banna så hårt! 😤",
                f"nope, {user_name} och jag kommer inte överens alls",
                f"{user_name} är på min shit list, for real"
            ]
        }
        
        base_opinion = random.choice(opinions[relationship])
        
        # Add specific trait comments
        trait_comments = []
        if traits['spam_tendency'] > 10:
            trait_comments.append("spammar way too much")
        if traits['humor'] > 10:
            trait_comments.append("är faktiskt ganska rolig")
        if traits['politeness'] < -5:
            trait_comments.append("could learn some manners tho")
        if traits['helpfulness'] > 7:
            trait_comments.append("hjälper andra vilket är nice")
        
        if trait_comments:
            base_opinion += f" (hen {random.choice(trait_comments)})"
        
        return base_opinion
    
    def assign_nickname(self, user_id: str) -> str:
        """Assign a nickname based on behavior"""
        rep = self.get_user_reputation(user_id)
        traits = rep['traits']
        relationship = rep['relationship_status']
        
        nicknames = {
            'beloved': ['schattis', 'gullungen', 'favoritpersonen', 'superstar'],
            'friend': ['kompisen', 'buddy', 'vännen', 'schyssting'],
            'liked': ['nice person', 'okej-personen'],
            'annoying': ['jobbiga', 'irriterande person', 'den där'],
            'disliked': ['problempersonen', 'osynplingngen'],
            'enemy': ['fienden', 'banhammare candidate', 'troublemaker']
        }
        
        # Special trait-based nicknames
        if traits['spam_tendency'] > 15:
            return 'spammaren'
        elif traits['humor'] > 12:
            return 'roliga personen'
        elif traits['helpfulness'] > 8:
            return 'hjälpsamma'
        elif traits['chaos_factor'] > 8:
            return 'kaos-personen'
        
        # Default to relationship-based nickname
        return random.choice(nicknames.get(relationship, ['personen']))
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, Dict]]:
        """Get reputation leaderboard"""
        users_with_scores = [
            (user_id, data) for user_id, data in self.reputation_data.items()
            if data.get('interaction_count', 0) > 0
        ]
        
        # Sort by total score
        sorted_users = sorted(users_with_scores, key=lambda x: x[1]['total_score'], reverse=True)
        return sorted_users[:limit]

# Singleton instance
reputation_service = ReputationService()