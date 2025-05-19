import time
import random
from telegram import Update
from telegram.ext import ContextTypes

from services.nlp_service import (
    update_chat_history, is_bot_mentioned, is_direct_question, should_respond_randomly,
    generate_response, save_chat_histories
)

from handlers.moderation import (
    check_for_spam, handle_spam_message
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle normal messages and check for bot mentions or trigger random replies"""
    print(f"DEBUG: Processing message from {update.effective_user.first_name}")
    
    # Skip processing for bot messages or commands
    if update.message.from_user.is_bot or update.message.text.startswith('/'):
        return
    
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text
    user_name = update.effective_user.first_name
    
    current_time = int(time.time())
    is_spamming = check_for_spam(user_id, current_time)
    update_chat_history(chat_id, user_id, "user", message_text)
    
    if is_spamming:
        await handle_spam_message(update, context, user_id, chat_id, message_text, user_name, current_time)
        return
    
    # Determine if the bot should respond for non-spam messages
    is_mentioned = is_bot_mentioned(message_text)
    is_question = is_direct_question(message_text)
    random_response = should_respond_randomly()
    
    should_respond = is_mentioned or is_question or random_response
    
    # Additional context
    if should_respond:
        response_context = ""
        if is_mentioned:
            response_context = "[Respond because your name was mentioned] "
        elif is_question:
            response_context = "[Respond because this is a direct question] "
        elif random_response:
            response_context = "[Respond with a random comment] "
        
        # Generate and send response
        response = generate_response(chat_id, user_id, response_context + message_text, user_name)
        await update.message.reply_text(response)
        
        # Debug
        print(f"Responded to {user_name}. Trigger: {'mention' if is_mentioned else 'question' if is_question else 'random'}")
        print(f"Message: '{message_text[:30]}...' Response: '{response[:30]}...'")
        
    # Save occasionally
    if random.random() < 0.05:
        save_chat_histories()
        print("Chat histories saved.")