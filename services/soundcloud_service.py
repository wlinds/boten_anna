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
        default_data = {
            "tracked_users": {},
            "last_check": None,
            "known_tracks": {},
            "my_account": None,
            "my_stats_history": [],
            "my_followers": {}  # {user_id: {username, display_name}}
        }

        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Convert known_tracks lists back to sets for efficient lookup
                if "known_tracks" in data:
                    for user_id, tracks in data["known_tracks"].items():
                        if isinstance(tracks, list):
                            data["known_tracks"][user_id] = set(tracks)

                # Ensure new fields exist
                if "my_account" not in data:
                    data["my_account"] = None
                if "my_stats_history" not in data:
                    data["my_stats_history"] = []
                if "my_followers" not in data:
                    data["my_followers"] = {}  # {user_id: {username, display_name}}

                return data
            except Exception as e:
                print(f"Error loading SoundCloud tracking data: {e}")
                return default_data
        return default_data
    
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

    def set_my_account(self, username: str) -> bool:
        """Set the account to track stats for (your own account)"""
        user_info = self._get_user_info(username)
        if user_info:
            self.tracking_data["my_account"] = {
                "user_id": str(user_info['id']),
                "username": user_info.get('permalink', username),
                "display_name": user_info.get('full_name', username),
                "permalink_url": user_info.get('permalink_url', f"https://soundcloud.com/{username}")
            }
            self._save_tracking_data()
            print(f"Set my account to: {username}")
            return True
        return False

    def _get_my_followers(self) -> Dict[str, Dict]:
        """Fetch current followers list from SoundCloud API"""
        if not self.tracking_data.get("my_account"):
            return {}

        user_id = self.tracking_data["my_account"]["user_id"]
        followers = {}

        try:
            # Fetch followers - paginate to get all
            next_href = f"{self.base_url}/users/{user_id}/followers"
            params = {"limit": 200, "linked_partitioning": 1}

            while next_href:
                data = self._make_api_request(next_href, params if "?" not in next_href else None)
                if not data:
                    break

                collection = data.get("collection", []) if isinstance(data, dict) else data
                for follower in collection:
                    if isinstance(follower, dict) and "id" in follower:
                        followers[str(follower["id"])] = {
                            "username": follower.get("permalink", follower.get("username", "unknown")),
                            "display_name": follower.get("full_name", follower.get("username", "unknown"))
                        }

                # Check for next page
                next_href = data.get("next_href") if isinstance(data, dict) else None
                params = None  # next_href includes params

        except Exception as e:
            print(f"Error fetching followers: {e}")

        return followers

    def _get_track_likers(self, track_id: int) -> Dict[str, Dict]:
        """Fetch users who liked a specific track"""
        likers = {}

        try:
            next_href = f"{self.base_url}/tracks/{track_id}/favoriters"
            params = {"limit": 200, "linked_partitioning": 1}

            while next_href:
                data = self._make_api_request(next_href, params if "?" not in next_href else None)
                if not data:
                    break

                collection = data.get("collection", []) if isinstance(data, dict) else data
                for liker in collection:
                    if isinstance(liker, dict) and "id" in liker:
                        likers[str(liker["id"])] = {
                            "username": liker.get("permalink", liker.get("username", "unknown")),
                            "display_name": liker.get("full_name", liker.get("username", "unknown"))
                        }

                next_href = data.get("next_href") if isinstance(data, dict) else None
                params = None

        except Exception as e:
            print(f"Error fetching track likers: {e}")

        return likers

    def get_my_account_stats(self) -> Optional[Dict]:
        """Get current stats for my account - per-track stats for detecting changes"""
        if not self.tracking_data.get("my_account"):
            return None

        user_id = self.tracking_data["my_account"]["user_id"]

        try:
            # Get user info for follower count
            user_info = self._make_api_request(f"{self.base_url}/users/{user_id}")
            if not user_info:
                return None

            # Get per-track stats
            track_stats = {}
            tracks = self._get_user_tracks(user_id, limit=50)
            for track in tracks:
                track_data = self._make_api_request(f"{self.base_url}/tracks/{track.id}")
                if track_data:
                    track_stats[str(track.id)] = {
                        "title": track.title,
                        "likes": track_data.get('likes_count', 0) or track_data.get('favoritings_count', 0) or 0,
                        "reposts": track_data.get('reposts_count', 0) or 0,
                        "plays": track_data.get('playback_count', 0) or 0
                    }

            stats = {
                "timestamp": datetime.now().isoformat(),
                "followers_count": user_info.get('followers_count', 0),
                "track_stats": track_stats
            }

            return stats

        except Exception as e:
            print(f"Error getting my account stats: {e}")
            return None

    def get_stats_changes(self) -> Optional[Dict]:
        """Compare current stats with previous stats and return specific changes"""
        current_stats = self.get_my_account_stats()
        if not current_stats:
            return None

        history = self.tracking_data.get("my_stats_history", [])
        previous_stats = history[-1] if history else None

        changes = {
            "new_followers": 0,
            "lost_followers": 0,
            "new_follower_names": [],  # List of display names of new followers
            "lost_follower_names": [],  # List of display names of lost followers
            "track_changes": []  # List of {track_title, new_likes, new_reposts, new_plays, new_liker_names}
        }

        # Get current followers list and compare with stored list
        current_followers = self._get_my_followers()
        stored_followers = self.tracking_data.get("my_followers", {})

        if current_followers:
            # Find new followers (in current but not in stored)
            for user_id, user_data in current_followers.items():
                if user_id not in stored_followers:
                    changes["new_follower_names"].append(user_data["display_name"])

            # Find lost followers (in stored but not in current)
            for user_id, user_data in stored_followers.items():
                if user_id not in current_followers:
                    changes["lost_follower_names"].append(user_data["display_name"])

            changes["new_followers"] = len(changes["new_follower_names"])
            changes["lost_followers"] = len(changes["lost_follower_names"])

            # Update stored followers
            self.tracking_data["my_followers"] = current_followers

        elif previous_stats:
            # Fallback to count-based detection if followers API failed
            prev_followers = previous_stats.get("followers_count", 0)
            curr_followers = current_stats.get("followers_count", 0)
            diff = curr_followers - prev_followers
            if diff > 0:
                changes["new_followers"] = diff
            elif diff < 0:
                changes["lost_followers"] = abs(diff)

        # Check per-track changes
        if previous_stats:
            prev_track_stats = previous_stats.get("track_stats", {})
            curr_track_stats = current_stats.get("track_stats", {})

            for track_id, curr_data in curr_track_stats.items():
                prev_data = prev_track_stats.get(track_id, {"likes": 0, "reposts": 0, "plays": 0})

                new_likes = curr_data["likes"] - prev_data.get("likes", 0)
                new_reposts = curr_data["reposts"] - prev_data.get("reposts", 0)
                new_plays = curr_data["plays"] - prev_data.get("plays", 0)

                if new_likes > 0 or new_reposts > 0:
                    track_change = {
                        "title": curr_data["title"],
                        "new_likes": new_likes if new_likes > 0 else 0,
                        "new_reposts": new_reposts if new_reposts > 0 else 0,
                        "new_plays": new_plays if new_plays > 0 else 0,
                        "new_liker_names": []
                    }

                    # Try to get who liked the track (only if there are new likes)
                    if new_likes > 0:
                        try:
                            current_likers = self._get_track_likers(int(track_id))
                            # We could store previous likers, but for now just show new likers count
                            # Getting specific new likers would require storing liker lists per track
                            # which might be expensive for many tracks
                        except Exception as e:
                            print(f"Error getting likers for track {track_id}: {e}")

                    changes["track_changes"].append(track_change)

        # Save current stats to history (keep last 30 entries)
        history.append(current_stats)
        if len(history) > 30:
            history = history[-30:]
        self.tracking_data["my_stats_history"] = history
        self._save_tracking_data()

        return changes

    def format_stats_update(self, changes: Dict) -> str:
        """Format stats changes as activity notifications"""
        if not changes:
            return ""

        lines = []

        # Follower changes - with names if available
        new_follower_names = changes.get("new_follower_names", [])
        lost_follower_names = changes.get("lost_follower_names", [])

        if new_follower_names:
            if len(new_follower_names) == 1:
                lines.append(f"New follower: {new_follower_names[0]}")
            elif len(new_follower_names) <= 3:
                names = ", ".join(new_follower_names)
                lines.append(f"New followers: {names}")
            else:
                # Show first 3 and count of remaining
                names = ", ".join(new_follower_names[:3])
                remaining = len(new_follower_names) - 3
                lines.append(f"New followers: {names} and {remaining} more")
        elif changes.get("new_followers", 0) > 0:
            # Fallback to count-only if names not available
            count = changes["new_followers"]
            if count == 1:
                lines.append("You gained a new follower!")
            else:
                lines.append(f"You gained {count} new followers!")

        if lost_follower_names:
            if len(lost_follower_names) == 1:
                lines.append(f"Lost follower: {lost_follower_names[0]}")
            elif len(lost_follower_names) <= 3:
                names = ", ".join(lost_follower_names)
                lines.append(f"Lost followers: {names}")
            else:
                names = ", ".join(lost_follower_names[:3])
                remaining = len(lost_follower_names) - 3
                lines.append(f"Lost followers: {names} and {remaining} more")
        elif changes.get("lost_followers", 0) > 0:
            count = changes["lost_followers"]
            if count == 1:
                lines.append("You lost a follower")
            else:
                lines.append(f"You lost {count} followers")

        # Track activity
        for track_change in changes.get("track_changes", []):
            title = track_change["title"]
            likes = track_change.get("new_likes", 0)
            reposts = track_change.get("new_reposts", 0)

            if likes > 0 and reposts > 0:
                if likes == 1 and reposts == 1:
                    lines.append(f"'{title}' got a new like and repost!")
                elif likes == 1:
                    lines.append(f"'{title}' got a new like and {reposts} reposts!")
                elif reposts == 1:
                    lines.append(f"'{title}' got {likes} new likes and a repost!")
                else:
                    lines.append(f"'{title}' got {likes} new likes and {reposts} reposts!")
            elif likes > 0:
                if likes == 1:
                    lines.append(f"'{title}' got a new like!")
                else:
                    lines.append(f"'{title}' got {likes} new likes!")
            elif reposts > 0:
                if reposts == 1:
                    lines.append(f"'{title}' got a new repost!")
                else:
                    lines.append(f"'{title}' got {reposts} new reposts!")

        if not lines:
            return ""

        return "**SoundCloud Activity**\n" + "\n".join(lines)


# Singleton instance
soundcloud_service = SoundCloudService()