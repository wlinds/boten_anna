import time
import random
from telegram import Update
from telegram.ext import ContextTypes

from services.nlp_service import (
    update_chat_history, is_bot_mentioned, is_direct_question, should_respond_randomly,
    generate_response, save_chat_histories
)
from handlers.moderation import (
    check_for_spam, handle_spam_message, message_counters
)
from services.user_service import user_service
from services.behavior_analyzer import behavior_analyzer
from services.reputation_service import reputation_service
from config.constants import SPAM_TIMEFRAME

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle normal messages and check for bot mentions or trigger random replies"""
    # Skip processing for bot messages or commands
    if update.message.from_user.is_bot or update.message.text.startswith('/'):
        return
    
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text
    user_name = update.effective_user.first_name
    
    # Update user information
    user_service.update_user(update.effective_user)
    
    # Analyze behavior for reputation system
    behavior_analyzer.analyze_message(user_id, message_text)
    
    # Update chat history
    update_chat_history(chat_id, user_id, "user", message_text)
    
    # Check for spam and analyze spam behavior
    current_time = int(time.time())
    is_spamming = check_for_spam(user_id, current_time)
    
    if is_spamming:
        message_count = len(message_counters.get(user_id, []))
        behavior_analyzer.analyze_spam_behavior(user_id, message_count, SPAM_TIMEFRAME)
        await handle_spam_message(update, context, user_id, chat_id, message_text, user_name, current_time)
        return
    
    # Determine if the bot should respond for non-spam messages
    is_mentioned = is_bot_mentioned(message_text)
    is_question = is_direct_question(message_text)
    random_response = should_respond_randomly()
    should_respond = is_mentioned or is_question or random_response
    
    if should_respond:
        # Get user's reputation for response modification
        user_rep = reputation_service.get_user_reputation(user_id)
        relationship = user_rep['relationship_status']
        
        # Add additional context about why the bot is responding
        response_context = ""
        if is_mentioned:
            response_context = "[Respond because your name was mentioned] "
        elif is_question:
            response_context = "[Respond because this is a direct question] "
        elif random_response:
            response_context = "[Respond with a random comment] "
        
        # Modify response context based on relationship with user
        if relationship == 'beloved':
            response_context += "[Be extra warm and friendly to this user - they're your favorite] "
        elif relationship == 'friend':
            response_context += "[Be friendly and casual with this user - you like them] "
        elif relationship == 'liked':
            response_context += "[Be pleasant with this user - you think they're okay] "
        elif relationship == 'neutral':
            response_context += "[Be normal with this user - no special opinion] "
        elif relationship == 'annoying':
            response_context += "[Be slightly sassy with this user - they can be annoying] "
        elif relationship == 'disliked':
            response_context += "[Be a bit cold with this user - you don't like them much] "
        elif relationship == 'enemy':
            response_context += "[Be stern and dismissive with this user - you really don't like them] "
        
        # Add trait-specific context for more nuanced responses
        traits = user_rep['traits']
        if traits['spam_tendency'] > 10:
            response_context += "[This user tends to spam - maybe mention that] "
        if traits['humor'] > 8:
            response_context += "[This user is funny - appreciate their humor] "
        if traits['politeness'] < -3:
            response_context += "[This user can be rude - call them out on it] "
        if traits['helpfulness'] > 5:
            response_context += "[This user is helpful - acknowledge that positively] "
        
        # Generate response with all context
        response = generate_response(chat_id, user_id, response_context + message_text, user_name)

        await update.message.reply_text(response)
        
        # Analyze user's response to Anna (sentiment analysis for reputation)
        if is_mentioned or random.random() < 0.2:  # Always analyze mentions, 20% chance for others
            # Simple sentiment analysis based on keywords
            positive_indicators = [
                'tack', 'bra', 'kul', 'rolig', 'schysst', 'nice', 'snäll', 'gullig',
                'thanks', 'good', 'great', 'awesome', 'cool', 'funny', 'sweet',
                '😊', '😄', '😆', '🤣', '😂', '❤️', '💕', '👍', '✅', '🔥'
            ]
            negative_indicators = [
                'dum', 'stupid', 'dålig', 'taskig', 'irriterande', 'jobbig',
                'bad', 'annoying', 'shut up', 'stfu', 'boring', 'lame',
                '😒', '😠', '😡', '🙄', '👎', '❌', '💩'
            ]
            
            positive_score = sum(1 for indicator in positive_indicators if indicator in message_text.lower())
            negative_score = sum(1 for indicator in negative_indicators if indicator in message_text.lower())
            
            if positive_score > negative_score and positive_score > 0:
                behavior_analyzer.analyze_response_to_anna(user_id, message_text, True)
            elif negative_score > positive_score and negative_score > 0:
                behavior_analyzer.analyze_response_to_anna(user_id, message_text, False)
        
        # Check if user helped someone (simple heuristic)
        helping_indicators = ['hjälp', 'help', 'försök', 'try this', 'kolla', 'check', 'här är', 'here is']
        if any(indicator in message_text.lower() for indicator in helping_indicators) and len(message_text) > 20:
            if random.random() < 0.3:  # 30% chance to register as helping
                behavior_analyzer.analyze_helpfulness(user_id, True)
        
        # Debug
        print(f"Responded to {user_name} ({relationship}). Trigger: {'mention' if is_mentioned else 'question' if is_question else 'random'}")
        print(f"Message: '{message_text[:30]}...' Response: '{response[:30]}...'")
        print(f"User reputation score: {user_rep['total_score']}")
        
    # Save occasionally
    if random.random() < 0.05:
        save_chat_histories()
        reputation_service._save_reputation()
        print("Chat histories and reputation data saved.")