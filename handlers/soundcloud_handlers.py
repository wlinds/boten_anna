import os, requests
from telegram import Update
from telegram.ext import ContextTypes

from services.soundcloud_service import soundcloud_service
from services.soundcloud_oauth_handler import SoundCloudOAuthHandler

async def soundcloud_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Setup SoundCloud authentication"""
    oauth_handler = SoundCloudOAuthHandler()
    
    # First try client credentials (doesn't need user auth)
    print("Attempting SoundCloud Client Credentials authentication...")
    token = oauth_handler.get_client_credentials_token()
    
    if token:
        await update.message.reply_text(
            "SoundCloud authentication successful!\n"
            "You can now use SoundCloud tracking commands."
        )
        return
    
    # If client credentials fail, provide authorization URL
    auth_url = oauth_handler.get_authorization_url()
    if auth_url:
        message = (
            "Client Credentials flow failed. You'll need user authorization.\n\n"
            f"Please visit this URL to authorize the bot:\n{auth_url}\n\n"
            "After authorization, you'll be redirected to localhost:8080/callback\n"
            "Copy the 'code' parameter from the URL and use:\n"
            "/sc_auth <code>"
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text(
            "SoundCloud setup failed. Please check your SOUNDCLOUD_CLIENT_ID in .env"
        )

async def soundcloud_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Complete SoundCloud authorization with code"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /sc_auth <authorization_code>\n"
            "Get the code from the redirect URL after visiting the authorization link."
        )
        return
    
    auth_code = context.args[0]
    oauth_handler = SoundCloudOAuthHandler()
    
    await update.message.reply_text("Exchanging authorization code for access token...")
    
    token = oauth_handler.exchange_code_for_token(auth_code)
    
    if token:
        await update.message.reply_text(
            "SoundCloud authorization successful!\n"
            "You can now use SoundCloud tracking commands."
        )
    else:
        await update.message.reply_text(
            "Authorization failed. Please try the setup process again."
        )

async def soundcloud_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check SoundCloud authentication status"""
    oauth_handler = SoundCloudOAuthHandler()
    
    # Check if we have a saved token
    saved_token = oauth_handler.get_saved_token()
    client_id = oauth_handler.client_id
    client_secret = oauth_handler.client_secret
    
    status_message = "**SoundCloud Status**\n\n"
    
    if client_id:
        status_message += f"Client ID: Configured\n"
    else:
        status_message += f"Client ID: Missing\n"
    
    if client_secret:
        status_message += f"Client Secret: Configured\n"
    else:
        status_message += f"Client Secret: Missing\n"
    
    if saved_token:
        # Test the token
        if oauth_handler.test_token(saved_token):
            status_message += f"Access Token: Valid\n"
        else:
            status_message += f"Access Token: Invalid/Expired\n"
    else:
        status_message += f"Access Token: None\n"
    
    # Show tracked users
    tracked_users = soundcloud_service.get_tracked_users()
    status_message += f"\n📊 Tracked Users: {len(tracked_users)}\n"
    
    if not client_id or not client_secret:
        status_message += "\nRun /sc_setup to configure authentication"
    elif not saved_token or not oauth_handler.test_token(saved_token):
        status_message += "\nRun /sc_setup to get access token"
    
    await update.message.reply_text(status_message)

async def soundcloud_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a SoundCloud user to track for new uploads"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /sc_follow <username> [display_name]\n"
            "You can also use full SoundCloud URLs."
        )
        return
    
    username = context.args[0]
    display_name = " ".join(context.args[1:]) if len(context.args) > 1 else None
    
    await update.message.reply_text(f"Adding {username} to SoundCloud tracking...")
    
    success = soundcloud_service.add_user_to_track(username, display_name)
    
    if success:
        display = display_name or username
        await update.message.reply_text(
            f"Now tracking {display} for new SoundCloud uploads!\n"
            f"I'll notify the chat when they post new tracks."
        )
        print(f"Added {username} to SoundCloud tracking")
    else:
        await update.message.reply_text(
            f"Failed to add {username} to tracking. "
            f"Make sure the username is correct.\n"
            f"If this persists, try /sc_setup to check authentication."
        )

async def soundcloud_untrack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a SoundCloud user from tracking"""
    if not context.args:
        await update.message.reply_text("Usage: /sc_unfollow <username>")
        return
    
    username = context.args[0]
    success = soundcloud_service.remove_user_from_tracking(username)
    
    if success:
        await update.message.reply_text(f"No longer following {username} for SoundCloud uploads.")
        print(f"Unfollowed {username}.")
    else:
        await update.message.reply_text(f"User {username} was not being followed.")

async def soundcloud_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all tracked SoundCloud users"""
    tracked_users = soundcloud_service.get_tracked_users()
    
    if not tracked_users:
        await update.message.reply_text("No SoundCloud users are currently being followed.")
        return
    
    message = "**Tracked SoundCloud Users:**\n\n"
    for user_id, user_data in tracked_users.items():
        message += f"• **{user_data['display_name']}** (@{user_data['username']})\n"
        message += f"  Added: {user_data['added_at'][:10]}\n"
        message += f"  Tracks: {user_data.get('track_count', 'Unknown')}\n\n"
    
    await update.message.reply_text(message)

async def soundcloud_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually check for new SoundCloud tracks"""
    await update.message.reply_text("Checking for new SoundCloud tracks...")
    
    new_tracks = soundcloud_service.check_for_new_tracks()
    
    if not new_tracks:
        await update.message.reply_text("No new tracks found from tracked users.")
        return
    
    await update.message.reply_text(f"Found {len(new_tracks)} new track(s)!")
    
    # Send notification for each new track
    for track_info in new_tracks:
        track = track_info["track"]
        user_data = track_info["user_data"]
        
        notification = soundcloud_service.format_track_notification(track, user_data)
        await update.message.reply_text(notification)


async def soundcloud_track_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add multiple SoundCloud users to track from a comma-separated list"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /sc_follow_all <username1,username2,username3>\n\n"
            "Note: Separate usernames with commas (no spaces around commas)"
        )
        return
    
    # Join all arguments and split by comma
    user_list_str = " ".join(context.args)
    usernames = [username.strip() for username in user_list_str.split(',') if username.strip()]
    
    if not usernames:
        await update.message.reply_text("No valid usernames found in the list.")
        return
    
    await update.message.reply_text(
        f"Starting bulk import of {len(usernames)} users...\n"
        f"This may take a moment, please wait..."
    )
    
    # Track results
    successful = []
    failed = []
    already_tracked = []
    
    # Check which users are already being tracked
    current_tracked = soundcloud_service.get_tracked_users()
    current_usernames = {data['username'].lower() for data in current_tracked.values()}
    
    for i, username in enumerate(usernames, 1):
        try:
            # Clean up the username
            clean_username = username.lower().strip()
            
            # Check if already tracked
            if clean_username in current_usernames:
                already_tracked.append(username)
                continue
            
            # Show progress for longer lists
            if len(usernames) > 5:
                progress_msg = f"({i}/{len(usernames)}) Adding {username}..."
                await update.message.reply_text(progress_msg)
            
            # Try to add the user
            success = soundcloud_service.add_user_to_track(username)
            
            if success:
                successful.append(username)
                print(f"Bulk import: Successfully added {username}")
            else:
                failed.append(username)
                print(f"Bulk import: Failed to add {username}")
                
        except Exception as e:
            failed.append(f"{username} (error: {str(e)})")
            print(f"Bulk import error for {username}: {e}")
    
    # Create summary report
    summary_lines = [
        "**Bulk Import Complete!**\n"
    ]
    
    if successful:
        summary_lines.append(f"**Successfully Added ({len(successful)}):**")
        for user in successful:
            summary_lines.append(f"  • {user}")
        summary_lines.append("")
    
    if already_tracked:
        summary_lines.append(f"**Already Tracked ({len(already_tracked)}):**")
        for user in already_tracked:
            summary_lines.append(f"  • {user}")
        summary_lines.append("")
    
    if failed:
        summary_lines.append(f"**Failed to Add ({len(failed)}):**")
        for user in failed:
            summary_lines.append(f"  • {user}")
        summary_lines.append("")
    
    # Add final stats
    total_now_tracked = len(soundcloud_service.get_tracked_users())
    summary_lines.append(f"🎵 **Total users now tracked:** {total_now_tracked}")
    
    if successful:
        summary_lines.append("\nNew tracks from these artists will be posted automatically!")
    
    # Send summary (split if too long)
    summary_text = "\n".join(summary_lines)
    
    if len(summary_text) > 4000:  # Telegram message limit
        # Split the summary into chunks
        chunk_size = 3500
        for i in range(0, len(summary_text), chunk_size):
            chunk = summary_text[i:i + chunk_size]
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(summary_text)

async def soundcloud_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Debug SoundCloud configuration"""
    oauth_handler = SoundCloudOAuthHandler()
    
    debug_info = [
        "**SoundCloud Debug Information**\n",
        f"Client ID: {oauth_handler.client_id[:10]}..." if oauth_handler.client_id else "Client ID: Missing",
        f"Client Secret: {'Present' if oauth_handler.client_secret else 'Missing'}",
        f"Redirect URI: {oauth_handler.redirect_uri}",
        f"Token file exists: {'Yes' if os.path.exists(oauth_handler.token_file) else 'No'}",
    ]

    debug_info.append("\n**Testing API Endpoints:**")
    test_endpoints = [
        "https://api.soundcloud.com/users/skrillex",
        "https://api-v2.soundcloud.com/users/skrillex",
        "https://api.soundcloud.com/resolve?url=https://soundcloud.com/skrillex"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(endpoint, params={'client_id': oauth_handler.client_id} if oauth_handler.client_id else {})
            status = f"{response.status_code}" if response.status_code == 200 else f"{response.status_code}"
            debug_info.append(f"{endpoint}: {status}")
        except Exception as e:
            debug_info.append(f"{endpoint}: Error - {str(e)}")

    debug_info.append("\n**Current Service State:**")
    
    has_token = "Yes" if soundcloud_service.access_token else "No"
    tracked_count = len(soundcloud_service.get_tracked_users())
    
    debug_info.extend([
        f"Has access token: {has_token}",
        f"Tracked users: {tracked_count}",
    ])

    debug_info.append("\n**Recommendations:**")
    if not oauth_handler.client_id or not oauth_handler.client_secret:
        debug_info.append("• Add SOUNDCLOUD_CLIENT_ID and SOUNDCLOUD_CLIENT_SECRET to .env")
    elif not soundcloud_service.access_token:
        debug_info.append("• Try changing redirect URI to: http://httpbin.org/get")
        debug_info.append("• Or run the callback server script to capture the auth code properly")
    else:
        debug_info.append("• Everything looks good! You can use /sc_follow")
    
    await update.message.reply_text("\n".join(debug_info))

async def soundcloud_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Refresh SoundCloud access token"""
    await update.message.reply_text("Attempting to refresh SoundCloud access token...")
    
    try:
        from services.soundcloud_oauth_handler import SoundCloudOAuthHandler
        oauth_handler = SoundCloudOAuthHandler()
        
        # Try to get a new token
        new_token = oauth_handler.get_client_credentials_token()
        
        if new_token:
            # Update the service with the new token
            from services.soundcloud_service import soundcloud_service
            soundcloud_service.access_token = new_token
            
            await update.message.reply_text(
                "Successfully refreshed SoundCloud access token!\n"
                "You can now use SoundCloud tracking commands again."
            )
        else:
            await update.message.reply_text(
                "Failed to refresh access token.\n"
                "You may need to run /sc_setup again to re-authenticate."
            )
            
    except Exception as e:
        await update.message.reply_text(f"Error refreshing token: {e}")

async def soundcloud_retry_failed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retry adding users that failed in the last bulk import"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /sc_retry_failed <comma-separated-list>\n\n"
            "Copy the failed usernames from your last bulk import:\n"
        )
        return
    
    await update.message.reply_text("First refreshing token, then retrying failed users...")
    
    # First refresh the token
    try:
        from services.soundcloud_oauth_handler import SoundCloudOAuthHandler
        oauth_handler = SoundCloudOAuthHandler()
        new_token = oauth_handler.get_client_credentials_token()
        
        if new_token:
            from services.soundcloud_service import soundcloud_service
            soundcloud_service.access_token = new_token
            await update.message.reply_text("Token refreshed! Now retrying users...")
        else:
            await update.message.reply_text("Token refresh failed, but will try anyway...")
    
    except Exception as e:
        await update.message.reply_text(f"Token refresh error: {e}, but will try anyway...")
    
    # Now retry the failed users using the bulk command logic
    user_list_str = " ".join(context.args)
    usernames = [username.strip() for username in user_list_str.split(',') if username.strip()]
    
    if not usernames:
        await update.message.reply_text("No valid usernames found in the list.")
        return
    
    successful = []
    failed = []
    
    for username in usernames:
        try:
            success = soundcloud_service.add_user_to_track(username)
            if success:
                successful.append(username)
            else:
                failed.append(username)
        except Exception as e:
            failed.append(f"{username} (error: {str(e)})")

    summary = ["**Retry Results:**\n"]
    
    if successful:
        summary.append(f"**Now Working ({len(successful)}):**")
        for user in successful:
            summary.append(f"  • {user}")
        summary.append("")
    
    if failed:
        summary.append(f"**Still Failed ({len(failed)}):**")
        for user in failed:
            summary.append(f"  • {user}")
    
    await update.message.reply_text("\n".join(summary))