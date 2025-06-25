import requests
import json
import os
from typing import Optional, Dict
from urllib.parse import urlencode, parse_qs, urlparse

class SoundCloudOAuthHandler:
    """Handle SoundCloud OAuth2 authentication flows"""
    
    def __init__(self):
        self.client_id = os.getenv('SOUNDCLOUD_CLIENT_ID')
        self.client_secret = os.getenv('SOUNDCLOUD_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SOUNDCLOUD_REDIRECT_URI', 'localhost:8080/callback')
        self.token_file = os.path.join(os.path.dirname(__file__), '../data/soundcloud_token.json')
        
    def get_client_credentials_token(self) -> Optional[str]:
        """
        Get access token using Client Credentials flow (for app-only access)
        This doesn't require user authorization and works for public data
        """
        if not self.client_id or not self.client_secret:
            print("Missing SoundCloud client_id or client_secret for OAuth")
            return None
            
        try:
            url = "https://api.soundcloud.com/oauth2/token"
            
            # Try different scope configurations
            scope_options = [
                None,  # No scope
                "",    # Empty scope
                "read",  # Basic read scope
                "*"    # Wildcard scope
            ]
            
            for scope in scope_options:
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
                
                # Only add scope if it's not None
                if scope is not None:
                    data['scope'] = scope
                
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                print(f"Trying client credentials with scope: {scope if scope is not None else 'no scope'}")
                
                response = requests.post(url, data=data, headers=headers)
                
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data.get('access_token')
                    
                    if access_token:
                        # Save token for future use
                        self._save_token_data(token_data)
                        print(f"✅ Successfully obtained SoundCloud access token with scope: {scope if scope is not None else 'no scope'}")
                        return access_token
                else:
                    print(f"❌ Scope '{scope}' failed: {response.status_code} - {response.text}")
                    
            print("❌ All scope options failed for Client Credentials flow")
            return None
                
        except Exception as e:
            print(f"Error in client credentials flow: {e}")
            return None
    
    def get_authorization_url(self) -> str:
        """
        Generate authorization URL for user authorization flow
        (Only needed if you want to access private user data)
        """
        if not self.client_id:
            return None
            
        params = {
            'client_id': self.client_id,
            'redirect_uri': f"http://{self.redirect_uri}",
            'response_type': 'code',
            'state': 'bot_auth'  # Remove the problematic scope
        }
        
        auth_url = f"https://soundcloud.com/connect?{urlencode(params)}"
        return auth_url
    
    def exchange_code_for_token(self, auth_code: str) -> Optional[str]:
        """
        Exchange authorization code for access token
        (For user authorization flow)
        """
        if not self.client_id or not self.client_secret:
            print("Missing client_id or client_secret for token exchange")
            return None
            
        try:
            url = "https://api.soundcloud.com/oauth2/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': f"http://{self.redirect_uri}",
                'code': auth_code
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            print(f"Attempting token exchange with:")
            print(f"- URL: {url}")
            print(f"- Client ID: {self.client_id}")
            print(f"- Redirect URI: http://{self.redirect_uri}")
            print(f"- Code length: {len(auth_code)}")
            
            response = requests.post(url, data=data, headers=headers)
            
            print(f"Token exchange response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if access_token:
                    self._save_token_data(token_data)
                    print("✅ Successfully obtained access token via authorization code")
                    return access_token
                else:
                    print("❌ No access token in successful response")
                    return None
            else:
                print(f"❌ Token exchange failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response (raw): {response.text}")
                return None
                    
        except Exception as e:
            print(f"Exception during token exchange: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _save_token_data(self, token_data: Dict):
        """Save token data to file"""
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            print(f"Error saving token: {e}")
    
    def _load_token_data(self) -> Optional[Dict]:
        """Load saved token data"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading token: {e}")
        return None
    
    def get_saved_token(self) -> Optional[str]:
        """Get previously saved access token"""
        token_data = self._load_token_data()
        if token_data:
            return token_data.get('access_token')
        return None
    
    def test_token(self, token: str) -> bool:
        """Test if a token is valid"""
        try:
            headers = {'Authorization': f'OAuth {token}'}
            response = requests.get('https://api.soundcloud.com/me', headers=headers)
            return response.status_code == 200
        except:
            return False