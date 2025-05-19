import time
from typing import Dict, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes
import traceback

from services.lyrics_service import get_kick_line
from config.constants import (
    SPAM_THRESHOLD, SPAM_TIMEFRAME, SPAM_WARNING_COOLDOWN, AUTO_KICK_THRESHOLD
)
from services.nlp_service import generate_response

# Message counter to track potential spam
message_counters = {}
spam_warning_sent = {}  # Track if a warning has been sent to a user
spam_warning_count = {}  # Track how many warnings a user has received

def check_for_spam(user_id: str, current_time: int) -> bool:
    """Check if a user is spamming based on message frequency"""

    print(f"DEBUG: Checking spam for {user_id}. Counter before: {message_counters.get(user_id, [])}")

    # Initialize counter for this user if not exists
    if user_id not in message_counters:
        message_counters[user_id] = []
    
    # Add current message timestamp
    message_counters[user_id].append(current_time)
    
    # Remove old messages outside the timeframe
    message_counters[user_id] = [t for t in message_counters[user_id] 
                                if current_time - t <= SPAM_TIMEFRAME]

    print(f"User {user_id} message count: {len(message_counters[user_id])} in last {SPAM_TIMEFRAME} seconds")
    
    return len(message_counters[user_id]) >= SPAM_THRESHOLD

def get_spam_warning_count(user_id: str) -> int:
    """Get the number of warnings a user has received"""
    return spam_warning_count.get(user_id, 0)

def record_spam_warning(user_id: str, current_time: int) -> int:
    """
    Record a spam warning for a user and return the warning count
    
    Args:
        user_id (str): User ID
        current_time (int): Current timestamp
        
    Returns:
        int: Updated warning count
    """
    # Update warning count
    if user_id not in spam_warning_count:
        spam_warning_count[user_id] = 1
    else:
        spam_warning_count[user_id] += 1
    
    # Record that we've sent a warning
    spam_warning_sent[user_id] = current_time
    
    return spam_warning_count[user_id]

def reset_spam_warning_count(user_id: str) -> None:
    """Reset the spam warning count for a user"""
    if user_id in spam_warning_count:
        spam_warning_count[user_id] = 0

def should_send_spam_warning(user_id: str, current_time: int) -> bool:
    """
    Check if we should send a spam warning to a user
    
    Args:
        user_id (str): User ID
        current_time (int): Current timestamp
        
    Returns:
        bool: True if we should send a warning, False otherwise
    """
    return (user_id not in spam_warning_sent or 
            current_time - spam_warning_sent[user_id] > SPAM_WARNING_COOLDOWN)

async def handle_spam_message(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              user_id: str, chat_id: str, message_text: str, 
                              user_name: str, current_time: int) -> None:
    """Handle a spam message"""
    print(f"DEBUG: Handling spam message from {user_name}. Warning count: {get_spam_warning_count(user_id)}")

    # Check if we should send a warning
    if should_send_spam_warning(user_id, current_time):
        warning_count = record_spam_warning(user_id, current_time)

        warning_context = (f"[This user has sent {len(message_counters[user_id])} messages in the last "
                          f"{SPAM_TIMEFRAME} seconds. This is warning #{warning_count}] {message_text}")
        
        # Generate and send response
        response = generate_response(chat_id, user_id, warning_context, user_name)
        await update.message.reply_text(response)
        
        print(f"Spam warning #{warning_count} sent to {user_name}")
        
        # Auto-kick ONLY if this is the third or greater warning
        if warning_count >= AUTO_KICK_THRESHOLD:
            await attempt_auto_kick(update, context, user_id, user_name)

async def attempt_auto_kick(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           user_id: str, user_name: str) -> None:
    """Attempt to auto-kick a user who has received too many spam warnings"""

    warning_count = get_spam_warning_count(user_id)
    
    # STRICT CHECK - only proceed if warning count is at least the threshold
    if warning_count < AUTO_KICK_THRESHOLD:
        print(f"DEBUG: Prevented auto-kick for {user_name} - warning count {warning_count} is below threshold {AUTO_KICK_THRESHOLD}")
        return
    
    print(f"DEBUG: Proceeding with auto-kick for {user_name} - warning count {warning_count} meets threshold {AUTO_KICK_THRESHOLD}")

    # Double-check that user has enough warnings before attempting to kick
    warning_count = get_spam_warning_count(user_id)
    if warning_count < AUTO_KICK_THRESHOLD:
        print(f"Warning: Attempted to kick {user_name} but warning count is only {warning_count}")
        return
        
    try:
        # Check if bot is admin
        chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        bot_me = await context.bot.get_me()
        
        bot_is_admin = any(admin.user.id == bot_me.id for admin in chat_admins)
        
            # Generate kick message using lyrics
            kick_line = get_kick_line()
            kick_line = lyrics_service.get_kick_line()
            kick_message = f"{kick_line} {user_name} har spammat för mycket. Jag röjer upp i våran kanal 🎵!"

            # Kick user
            await context.bot.ban_chat_member(update.effective_chat.id, update.effective_user.id)
            
            # Immediately unban so they can rejoin
            await context.bot.unban_chat_member(
                update.effective_chat.id, 
                update.effective_user.id,
                only_if_banned=True
            )
            
            reset_spam_warning_count(user_id)
            await update.message.reply_text(kick_message)
            print(f"Auto-kicked user {user_name} for excessive spam")
        else:
            await update.message.reply_text(
                f"jag vill kicka {user_name} för spam, men jag har inte admin-rättigheter. någon admin får göra det åt mig!"
            )
    except Exception as e:
        print(f"Failed to kick user: {str(e)}")
        await update.message.reply_text(
            f"försökte kicka {user_name} men något gick fel: {str(e)}"
        )