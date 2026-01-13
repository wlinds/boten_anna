import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock


class TestSoundCloudService:
    """Tests for SoundCloud service stats tracking"""

    @pytest.fixture
    def service(self, tmp_path, monkeypatch):
        """Create a SoundCloudService instance with mocked dependencies"""
        monkeypatch.setenv("SOUNDCLOUD_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("SOUNDCLOUD_CLIENT_SECRET", "test_client_secret")

        with patch.dict("sys.modules", {"services.soundcloud_oauth_handler": MagicMock()}):
            from services.soundcloud_service import SoundCloudService

            with patch.object(SoundCloudService, "__init__", lambda x: None):
                service = SoundCloudService()
                service.client_id = "test_client_id"
                service.client_secret = "test_client_secret"
                service.access_token = "test_token"
                service.base_url = "https://api.soundcloud.com"
                service.api_v2_url = "https://api-v2.soundcloud.com"
                service.data_path = str(tmp_path / "soundcloud_tracking.json")
                service.tracking_data = {
                    "tracked_users": {},
                    "last_check": None,
                    "known_tracks": {},
                    "my_account": None,
                    "my_stats_history": []
                }
                service.oauth_handler = None
                return service

    def test_set_my_account_success(self, service):
        """Test setting my account successfully"""
        mock_user_info = {
            "id": 12345,
            "permalink": "testuser",
            "full_name": "Test User",
            "permalink_url": "https://soundcloud.com/testuser"
        }

        with patch.object(service, "_get_user_info", return_value=mock_user_info):
            with patch.object(service, "_save_tracking_data"):
                result = service.set_my_account("testuser")

        assert result is True
        assert service.tracking_data["my_account"] is not None
        assert service.tracking_data["my_account"]["user_id"] == "12345"

    def test_set_my_account_failure(self, service):
        """Test setting my account when user not found"""
        with patch.object(service, "_get_user_info", return_value=None):
            result = service.set_my_account("nonexistent")

        assert result is False
        assert service.tracking_data["my_account"] is None

    def test_get_my_account_stats_no_account(self, service):
        """Test getting stats when no account is set"""
        result = service.get_my_account_stats()
        assert result is None

    def test_get_stats_changes_new_follower(self, service):
        """Test detecting new followers"""
        service.tracking_data["my_account"] = {"user_id": "12345", "username": "testuser"}
        service.tracking_data["my_stats_history"] = [{
            "timestamp": "2026-01-12T10:00:00",
            "followers_count": 100,
            "track_stats": {}
        }]

        mock_current_stats = {
            "timestamp": "2026-01-13T10:00:00",
            "followers_count": 102,
            "track_stats": {}
        }

        with patch.object(service, "get_my_account_stats", return_value=mock_current_stats):
            with patch.object(service, "_save_tracking_data"):
                result = service.get_stats_changes()

        assert result["new_followers"] == 2
        assert result["lost_followers"] == 0

    def test_get_stats_changes_lost_follower(self, service):
        """Test detecting lost followers"""
        service.tracking_data["my_account"] = {"user_id": "12345", "username": "testuser"}
        service.tracking_data["my_stats_history"] = [{
            "timestamp": "2026-01-12T10:00:00",
            "followers_count": 100,
            "track_stats": {}
        }]

        mock_current_stats = {
            "timestamp": "2026-01-13T10:00:00",
            "followers_count": 98,
            "track_stats": {}
        }

        with patch.object(service, "get_my_account_stats", return_value=mock_current_stats):
            with patch.object(service, "_save_tracking_data"):
                result = service.get_stats_changes()

        assert result["new_followers"] == 0
        assert result["lost_followers"] == 2

    def test_get_stats_changes_new_likes_on_track(self, service):
        """Test detecting new likes on a track"""
        service.tracking_data["my_account"] = {"user_id": "12345", "username": "testuser"}
        service.tracking_data["my_stats_history"] = [{
            "timestamp": "2026-01-12T10:00:00",
            "followers_count": 100,
            "track_stats": {
                "111": {"title": "My Song", "likes": 10, "reposts": 2, "plays": 500}
            }
        }]

        mock_current_stats = {
            "timestamp": "2026-01-13T10:00:00",
            "followers_count": 100,
            "track_stats": {
                "111": {"title": "My Song", "likes": 13, "reposts": 2, "plays": 550}
            }
        }

        with patch.object(service, "get_my_account_stats", return_value=mock_current_stats):
            with patch.object(service, "_save_tracking_data"):
                result = service.get_stats_changes()

        assert len(result["track_changes"]) == 1
        assert result["track_changes"][0]["title"] == "My Song"
        assert result["track_changes"][0]["new_likes"] == 3
        assert result["track_changes"][0]["new_reposts"] == 0

    def test_get_stats_changes_new_reposts_on_track(self, service):
        """Test detecting new reposts on a track"""
        service.tracking_data["my_account"] = {"user_id": "12345", "username": "testuser"}
        service.tracking_data["my_stats_history"] = [{
            "timestamp": "2026-01-12T10:00:00",
            "followers_count": 100,
            "track_stats": {
                "111": {"title": "My Song", "likes": 10, "reposts": 2, "plays": 500}
            }
        }]

        mock_current_stats = {
            "timestamp": "2026-01-13T10:00:00",
            "followers_count": 100,
            "track_stats": {
                "111": {"title": "My Song", "likes": 10, "reposts": 5, "plays": 550}
            }
        }

        with patch.object(service, "get_my_account_stats", return_value=mock_current_stats):
            with patch.object(service, "_save_tracking_data"):
                result = service.get_stats_changes()

        assert len(result["track_changes"]) == 1
        assert result["track_changes"][0]["new_reposts"] == 3

    def test_format_stats_update_single_follower_with_name(self, service):
        """Test formatting single new follower with name"""
        changes = {
            "new_followers": 1,
            "lost_followers": 0,
            "new_follower_names": ["John Doe"],
            "lost_follower_names": [],
            "track_changes": []
        }
        result = service.format_stats_update(changes)
        assert "New follower: John Doe" in result

    def test_format_stats_update_multiple_followers_with_names(self, service):
        """Test formatting multiple new followers with names"""
        changes = {
            "new_followers": 3,
            "lost_followers": 0,
            "new_follower_names": ["Alice", "Bob", "Charlie"],
            "lost_follower_names": [],
            "track_changes": []
        }
        result = service.format_stats_update(changes)
        assert "New followers: Alice, Bob, Charlie" in result

    def test_format_stats_update_many_followers_with_names(self, service):
        """Test formatting many new followers shows first 3 and count"""
        changes = {
            "new_followers": 5,
            "lost_followers": 0,
            "new_follower_names": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
            "lost_follower_names": [],
            "track_changes": []
        }
        result = service.format_stats_update(changes)
        assert "New followers: Alice, Bob, Charlie and 2 more" in result

    def test_format_stats_update_single_follower_fallback(self, service):
        """Test formatting single new follower without name (fallback)"""
        changes = {"new_followers": 1, "lost_followers": 0, "new_follower_names": [], "lost_follower_names": [], "track_changes": []}
        result = service.format_stats_update(changes)
        assert "You gained a new follower!" in result

    def test_format_stats_update_multiple_followers_fallback(self, service):
        """Test formatting multiple new followers without names (fallback)"""
        changes = {"new_followers": 5, "lost_followers": 0, "new_follower_names": [], "lost_follower_names": [], "track_changes": []}
        result = service.format_stats_update(changes)
        assert "You gained 5 new followers!" in result

    def test_format_stats_update_lost_follower_with_name(self, service):
        """Test formatting lost follower with name"""
        changes = {
            "new_followers": 0,
            "lost_followers": 1,
            "new_follower_names": [],
            "lost_follower_names": ["Jane Smith"],
            "track_changes": []
        }
        result = service.format_stats_update(changes)
        assert "Lost follower: Jane Smith" in result

    def test_format_stats_update_lost_follower_fallback(self, service):
        """Test formatting lost follower without name (fallback)"""
        changes = {"new_followers": 0, "lost_followers": 1, "new_follower_names": [], "lost_follower_names": [], "track_changes": []}
        result = service.format_stats_update(changes)
        assert "You lost a follower" in result

    def test_format_stats_update_single_like(self, service):
        """Test formatting single new like on track"""
        changes = {
            "new_followers": 0,
            "lost_followers": 0,
            "track_changes": [{"title": "My Song", "new_likes": 1, "new_reposts": 0}]
        }
        result = service.format_stats_update(changes)
        assert "'My Song' got a new like!" in result

    def test_format_stats_update_multiple_likes(self, service):
        """Test formatting multiple likes on track"""
        changes = {
            "new_followers": 0,
            "lost_followers": 0,
            "track_changes": [{"title": "My Song", "new_likes": 5, "new_reposts": 0}]
        }
        result = service.format_stats_update(changes)
        assert "'My Song' got 5 new likes!" in result

    def test_format_stats_update_likes_and_reposts(self, service):
        """Test formatting likes and reposts together"""
        changes = {
            "new_followers": 0,
            "lost_followers": 0,
            "track_changes": [{"title": "My Song", "new_likes": 3, "new_reposts": 2}]
        }
        result = service.format_stats_update(changes)
        assert "'My Song' got 3 new likes and 2 reposts!" in result

    def test_format_stats_update_empty(self, service):
        """Test formatting with no changes"""
        changes = {"new_followers": 0, "lost_followers": 0, "track_changes": []}
        result = service.format_stats_update(changes)
        assert result == ""

    def test_format_stats_update_none(self, service):
        """Test formatting with None input"""
        result = service.format_stats_update(None)
        assert result == ""
