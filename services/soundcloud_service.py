import requests
import json
import os
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class SoundCloudTrack:
    id: int
    title: str
    user: str
    user_id: int
    permalink_url: str
    created_at: str
    duration: int
    genre: Optional[str] = None
    description: Optional[str] = None

class SoundCloudService:
    """Service for monitoring SoundCloud user uploads"""
    
    def __init__(self):
        self.client_id = os.getenv('SOUNDCLOUD_CLIENT_ID')
        self.client_secret = os.getenv('SOUNDCLOUD_CLIENT_SECRET')
        self.access_token = os.getenv('SOUNDCLOUD_ACCESS_TOKEN')
        self.base_url = 'https://api.soundcloud.com'
        self.api_v2_url = 'https://api-v2.soundcloud.com'
        self.data_path = os.path.join(os.path.dirname(__file__), '../data/soundcloud_tracking.json')
        self.tracking_data = self._load_tracking_data()
        
        # Initialize OAuth handler
        try:
            from services.soundcloud_oauth_handler import SoundCloudOAuthHandler
            self.oauth_handler = SoundCloudOAuthHandler()
        except ImportError:
            print("Could not import SoundCloudOAuthHandler")
            self.oauth_handler = None
        
        # Try to get access token in order of preference
        if not self.access_token and self.oauth_handler:
            # 1. Try saved token first
            self.access_token = self.oauth_handler.get_saved_token()
            
            # 2. If no saved token, try client credentials
            if not self.access_token and self.client_id and self.client_secret:
                print("No saved token found, attempting Client Credentials flow...")
                self.access_token = self.oauth_handler.get_client_credentials_token()
        
        if not self.access_token:
            print("No valid access token available")
        
        if not self.client_id:
            print("Warning: SOUNDCLOUD_CLIENT_ID not found in environment variables")
            print("SoundCloud functionality will be limited")
    
    def _load_tracking_data(self) -> Dict:
        """Load tracking data from file"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convert known_tracks lists back to sets for efficient lookup
                if "known_tracks" in data:
                    for user_id, tracks in data["known_tracks"].items():
                        if isinstance(tracks, list):
                            data["known_tracks"][user_id] = set(tracks)
                
                return data
            except Exception as e:
                print(f"Error loading SoundCloud tracking data: {e}")
                return {"tracked_users": {}, "last_check": None, "known_tracks": {}}
        return {"tracked_users": {}, "last_check": None, "known_tracks": {}}
    
    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            # Create a copy of tracking data for JSON serialization
            data_to_save = self.tracking_data.copy()
            
            # Convert sets to lists for JSON serialization
            if "known_tracks" in data_to_save:
                data_to_save["known_tracks"] = {
                    user_id: list(tracks) if isinstance(tracks, set) else tracks
                    for user_id, tracks in data_to_save["known_tracks"].items()
                }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving SoundCloud tracking data: {e}")

    def add_user_to_track(self, username: str, display_name: str = None) -> bool:
        """
        Add a SoundCloud user to track for new uploads
        
        Args:
            username (str): SoundCloud username or URL
            display_name (str): Optional display name for notifications
            
        Returns:
            bool: True if user was added successfully
        """
        # Extract username from URL if provided
        if 'soundcloud.com/' in username:
            username = username.split('soundcloud.com/')[-1].split('?')[0]
        
        try:
            # Get user info from SoundCloud API
            user_info = self._get_user_info(username)
            
            if not user_info:
                print(f"Could not find user {username}")
                return False
            
            user_id = str(user_info['id'])
            self.tracking_data["tracked_users"][user_id] = {
                "username": user_info.get('permalink', user_info.get('username', username)),
                "display_name": display_name or user_info.get('full_name', username),
                "permalink_url": user_info.get('permalink_url', f"https://soundcloud.com/{username}"),
                "added_at": datetime.now().isoformat(),
                "track_count": user_info.get('track_count', 0),
                "use_scraping": False  # Always false since we removed scraping
            }
            
            # Initialize known tracks for this user
            if user_id not in self.tracking_data["known_tracks"]:
                self.tracking_data["known_tracks"][user_id] = set()
                # Get existing tracks to avoid notifying about old content
                existing_tracks = self._get_user_tracks(user_id)
                
                print(f"Found {len(existing_tracks)} existing tracks for {username}")
                for track in existing_tracks:
                    self.tracking_data["known_tracks"][user_id].add(track.id)
            
            self._save_tracking_data()
            print(f"Successfully added {username} to tracking")
            return True
            
        except Exception as e:
            print(f"Error adding user to track: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_user_from_tracking(self, username: str) -> bool:
        """Remove a user from tracking"""
        # Find user by username
        user_id_to_remove = None
        for user_id, user_data in self.tracking_data["tracked_users"].items():
            if user_data["username"].lower() == username.lower():
                user_id_to_remove = user_id
                break
        
        if user_id_to_remove:
            del self.tracking_data["tracked_users"][user_id_to_remove]
            if user_id_to_remove in self.tracking_data["known_tracks"]:
                del self.tracking_data["known_tracks"][user_id_to_remove]
            self._save_tracking_data()
            return True
        return False
    
    def get_tracked_users(self) -> Dict:
        """Get list of currently tracked users"""
        return self.tracking_data["tracked_users"].copy()
    
    def check_for_new_tracks(self) -> List[Dict]:
        """
        Check all tracked users for new tracks
        
        Returns:
            List[Dict]: List of new tracks with user info
        """
        if not self.access_token:
            print("No access token available for checking tracks")
            return []
        
        new_tracks = []
        
        for user_id, user_data in self.tracking_data["tracked_users"].items():
            try:
                # Get recent tracks for this user
                tracks = self._get_user_tracks(user_id, limit=20)
                
                # Ensure known_tracks is a set
                if user_id not in self.tracking_data["known_tracks"]:
                    self.tracking_data["known_tracks"][user_id] = set()
                elif isinstance(self.tracking_data["known_tracks"][user_id], list):
                    # Convert from list to set (backwards compatibility)
                    self.tracking_data["known_tracks"][user_id] = set(self.tracking_data["known_tracks"][user_id])
                
                known_track_ids = self.tracking_data["known_tracks"][user_id]
                
                # Check for new tracks
                for track in tracks:
                    if track.id not in known_track_ids:
                        # This is a new track!
                        new_tracks.append({
                            "track": track,
                            "user_data": user_data
                        })
                        
                        # Add to known tracks
                        known_track_ids.add(track.id)
                
            except Exception as e:
                print(f"Error checking tracks for user {user_id}: {e}")
                continue
        
        # Update last check time and save
        self.tracking_data["last_check"] = datetime.now().isoformat()
        self._save_tracking_data()
        
        return new_tracks
    
    def format_track_notification(self, track: SoundCloudTrack, user_data: Dict) -> str:
        """Format a track notification message"""
        duration_minutes = track.duration // 60000 if track.duration else 0  # Convert from milliseconds
        duration_seconds = (track.duration % 60000) // 1000 if track.duration else 0
        
        # Parse creation date
        try:
            created_date = datetime.fromisoformat(track.created_at.replace('Z', '+00:00'))
            time_str = created_date.strftime('%Y-%m-%d %H:%M')
        except:
            time_str = "Unknown time"
        
        message = f"🎵 **New track from {user_data['display_name']}!**\n\n"
        message += f"**{track.title}**\n"
        
        if track.duration and track.duration > 0:
            message += f"Duration: {duration_minutes:02d}:{duration_seconds:02d}\n"
        
        if track.genre:
            message += f"Genre: {track.genre}\n"
        
        message += f"Posted: {time_str}\n"
        message += f"🔗 {track.permalink_url}\n"
        
        if track.description and len(track.description) < 200:
            message += f"\n_{track.description}_"
        
        return message
    
    def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated API request"""
        headers = {}
        if self.access_token:
            headers['Authorization'] = f'OAuth {self.access_token}'
        
        if params is None:
            params = {}
        
        # Add client_id as fallback
        if not self.access_token and self.client_id:
            params['client_id'] = self.client_id
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print(f"Authentication failed for SoundCloud API. Status: {response.status_code}")
                # Try to refresh token if we have OAuth handler
                if hasattr(self, 'oauth_handler') and self.oauth_handler:
                    print("Attempting to refresh access token...")
                    new_token = self.oauth_handler.get_client_credentials_token()
                    if new_token:
                        self.access_token = new_token
                        headers['Authorization'] = f'OAuth {new_token}'
                        response = requests.get(url, params=params, headers=headers, timeout=10)
                        if response.status_code == 200:
                            return response.json()
                print(f"Authentication still failing. Token may need manual refresh.")
                return None
            else:
                print(f"SoundCloud API error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.Timeout:
            print(f"Request timed out for URL: {url}")
            return None
        except Exception as e:
            print(f"Error making API request: {e}")
            return None
    
    def _get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information from SoundCloud API"""
        # Try multiple API endpoints and methods
        endpoints_to_try = [
            # Method 1: Resolve URL
            {
                'url': f"{self.base_url}/resolve",
                'params': {'url': f'https://soundcloud.com/{username}'}
            },
            # Method 2: Direct user lookup
            {
                'url': f"{self.base_url}/users/{username}",
                'params': {}
            },
            # Method 3: Search for user
            {
                'url': f"{self.base_url}/users",
                'params': {'q': username, 'limit': 1}
            }
        ]
        
        for method in endpoints_to_try:
            try:
                result = self._make_api_request(method['url'], method['params'])
                if result:
                    # Handle different response formats
                    if isinstance(result, list) and len(result) > 0:
                        # Search results
                        user_data = result[0]
                    elif isinstance(result, dict) and 'id' in result:
                        # Direct user object
                        user_data = result
                    else:
                        continue
                    
                    # Validate this is the right user
                    if (user_data.get('permalink') == username or 
                        user_data.get('username') == username):
                        return user_data
                        
            except Exception as e:
                print(f"Error trying endpoint {method['url']}: {e}")
                continue
        
        print(f"Could not find user {username} on any SoundCloud API endpoint")
        return None
    
    def _get_user_tracks(self, user_id: str, limit: int = 50) -> List[SoundCloudTrack]:
        """Get tracks for a specific user"""
        # Try multiple methods to get user tracks
        methods_to_try = [
            # Method 1: Direct tracks endpoint
            {
                'url': f"{self.base_url}/users/{user_id}/tracks",
                'params': {'limit': limit, 'linked_partitioning': 1}
            },
            # Method 2: V2 API
            {
                'url': f"{self.api_v2_url}/users/{user_id}/tracks", 
                'params': {'limit': limit}
            },
            # Method 3: Search for tracks by user (fallback)
            {
                'url': f"{self.base_url}/tracks",
                'params': {'user_id': user_id, 'limit': limit}
            }
        ]
        
        for method in methods_to_try:
            try:
                data = self._make_api_request(method['url'], method['params'])
                if data:
                    tracks = []
                    
                    # Handle different response formats
                    if isinstance(data, dict) and 'collection' in data:
                        collection = data['collection']
                    elif isinstance(data, list):
                        collection = data
                    else:
                        continue
                    
                    for track_data in collection:
                        try:
                            track = SoundCloudTrack(
                                id=track_data['id'],
                                title=track_data['title'],
                                user=track_data['user']['username'] if 'user' in track_data else 'unknown',
                                user_id=track_data['user']['id'] if 'user' in track_data else user_id,
                                permalink_url=track_data['permalink_url'],
                                created_at=track_data['created_at'],
                                duration=track_data.get('duration', 0),
                                genre=track_data.get('genre'),
                                description=track_data.get('description')
                            )
                            tracks.append(track)
                        except KeyError as e:
                            print(f"Error parsing track data, missing field: {e}")
                            continue
                    
                    if tracks:  # If we got some tracks, return them
                        return tracks
                        
            except Exception as e:
                print(f"Error trying tracks method {method['url']}: {e}")
                continue
        
        print(f"Could not fetch tracks for user {user_id} from any endpoint")
        return []

# Singleton instance
soundcloud_service = SoundCloudService()