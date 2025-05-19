import numpy as np
import random
import threading
import requests
import time
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from utils.env_utils import get_env_vars
from utils.misc_utils import welcome_message, google_search
from utils.time_utils import convert_to_gmt
from services.weather_service import get_weather
from services.pollen_service import get_pollen_for_location
from services.nlp_service import generate_response, save_chat_histories
from services.lyrics_service import lyrics_service
from data.chat_store import chat_store
from data.personality_trainer import personality_trainer

TOKEN, CHAT_ID, _, _, _, _ = get_env_vars()

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets the user with a welcome_message located in misc.py"""
    greeting_line = lyrics_service.get_greeting_line()
    await update.message.reply_text(f'{welcome_message()}, {update.effective_user.first_name}! {greeting_line}')

async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roll a dice with specified number of sides"""
    command_text = update.message.text.strip() 
    highest = 100

    print(f'{update.effective_user.first_name} requested {command_text=}.')

    if len(command_text.split()) > 1:
        try:
            highest = int(command_text.split()[1])
            if highest <= 0:
                raise ValueError("Highest number must be a positive integer.")
        except ValueError:
            await update.message.reply_text(f"Can't roll die with {highest} sides. Try a positive integer.")
            return

    # Handle case if someone decides to roll one-sided dice
    if highest == 1:
        roll = 1
    else:
        roll = np.random.randint(1, highest + 1)

    await update.message.reply_text(f'{update.effective_user.first_name} rolls {roll} (1-{highest})')
    print(f'Success. {roll=}.')

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather updates for a specified city"""
    print(f'{update.effective_user.first_name} requested /weather.')
    city = ' '.join(context.args)
    
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info)

async def googlar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search Google for a query"""
    query = ' '.join(context.args)
    print(f'{update.effective_user.first_name} requested /google with {query=}.')
    
    if not query:
        print(f'No search query selected.')
        await update.message.reply_text("Please provide a search query.")
        return

    search_results = google_search(query, verbose=True)
    await update.message.reply_text(search_results)

async def start_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a timer for the given number of seconds"""
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Invalid timer command. Usage: /timer <seconds>")
        return

    try:
        seconds = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid timer duration. Please provide a valid number of seconds.")
        return
    
    # Store the chat_id and user_name for when the timer completes
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    
    # Schedule the timer task with this specific chat's ID
    threading.Timer(seconds, timer_done, args=[chat_id, user_name, context.bot]).start()

    await update.message.reply_text(f"Timer started for {seconds} seconds.")
    print(f"Timer set by {user_name} for {seconds} seconds.")

def timer_done(chat_id: int, user_name: str, bot) -> None:
    """Sends a notification when a timer is done"""
    message = f"⏰ DING DONG! Timer set by {user_name} is done!"
    
    # Use the bot's async methods in a non-async function
    import asyncio
    
    async def send_timer_notification():
        await bot.send_message(chat_id=chat_id, text=message)
    
    # Create and run an event loop to send the message
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in this thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(send_timer_notification())
    
    print(message)

async def add_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds item to list"""
    # Get the item from the user's message
    item = " ".join(context.args)

    if not item:
        await update.message.reply_text("Please provide an item to add to the list.")
        return

    chat_id = str(update.effective_chat.id)
    chat_store.add_item_to_list(chat_id, item)

    # Reply with a confirmation message
    await update.message.reply_text(f"Item '{item}' added to the list.")

async def remove_from_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removes item from list"""
    # Get the item to be removed
    item = " ".join(context.args)

    if not item:
        await update.message.reply_text("Please provide an item to remove from the list.")
        return

    chat_id = str(update.effective_chat.id)
    items = chat_store.get_chat_list(chat_id)
    
    if not items:
        await update.message.reply_text("The list is empty.")
        return
    
    if chat_store.remove_item_from_list(chat_id, item):
        await update.message.reply_text(f"Item '{item}' removed from the list.")
    else:
        await update.message.reply_text(f"Item '{item}' not found in the list.")

async def clear_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the entire list"""
    chat_id = str(update.effective_chat.id)
    items = chat_store.get_chat_list(chat_id)
    
    if not items:
        await update.message.reply_text("The list is already empty.")
        return

    chat_store.clear_list(chat_id)
    await update.message.reply_text("The list has been cleared.")
  
async def display_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the items in the list"""
    chat_id = str(update.effective_chat.id)
    items = chat_store.get_chat_list(chat_id)
    
    if not items:
        await update.message.reply_text("The list is empty.")
        return

    # Format the items as a string
    items_str = "\n".join(items)

    # Send the formatted list as a message
    await update.message.reply_text(f"The list contains:\n{items_str}")

async def pollenrapport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get pollen information for a specified city"""
    location = ' '.join(context.args) or "gothenburg"
    days = 3
    
    print(f'{update.effective_user.first_name} requested /pollen for {location}.')
    
    message = get_pollen_for_location(location, days)
    await update.message.reply_text(message)
    print(f'Pollen information for {location} provided.')

async def time_convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert time from a specified timezone to GMT+2"""
    input_time = " ".join(context.args)
    result = convert_to_gmt(input_time)

    await update.message.reply_text(result)

async def chat_with_anna(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Direct chat with Anna using NLP"""
    print(f'{update.effective_user.first_name} requested /chat.')
    
    # Get the message to chat about
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("What would you like to chat about?")
        return
    
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    user_name = update.effective_user.first_name
    
    # Generate and send response
    response = generate_response(chat_id, user_id, message, user_name)
    await update.message.reply_text(response)
    print(f'Chat response provided for message: {message[:30]}...')

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the status and personality of the bot"""
    print(f'{update.effective_user.first_name} requested /status.')
    
    # Get character configuration summary
    config_path = os.path.join(os.path.dirname(__file__), '../config/character_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    personality = config['demographics']['name']
    age = config['demographics']['age']
    location = config['demographics']['location']
    
    # Get common phrases
    common_phrases = config['linguistic_profile']['speech_patterns'].get('common_phrases', [])
    phrase_text = ', '.join(f'"{phrase}"' for phrase in common_phrases[:3]) if common_phrases else "None defined"
    
    # Get personality data summary
    personality_summary = personality_trainer.get_personality_summary()
    
    # Create status message
    status_message = (
        f"🤖 **Bot Status Report** 🤖\n\n"
        f"Name: {personality}\n"
        f"Age: {age}\n"
        f"Location: {location}\n"
        f"Common phrases: {phrase_text}\n\n"
        f"{personality_summary}\n\n"
        f"I've been learning from our conversations to better suit your chat's needs!"
    )
    
    await update.message.reply_text(status_message)
    print(f'Status information provided.')

async def toggle_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle the bot's personality traits"""
    
    print(f'{update.effective_user.first_name} requested /personality.')
    
    # Get the personality trait to toggle
    args = context.args
    if not args or len(args) < 1:
        trait_options = [
            "emoji_usage (current: moderate/rare/frequent)", 
            "humor_style (current: dry/silly/sarcastic)",
            "talkativeness (current: low/medium/high)"
        ]
        await update.message.reply_text(
            "Please specify which personality trait to toggle:\n" + 
            "\n".join(f"- {trait}" for trait in trait_options)
        )
        return
    
    trait = args[0].lower()
    value = args[1].lower() if len(args) > 1 else None
    
    config_path = os.path.join(os.path.dirname(__file__), '../config/character_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if trait == "emoji_usage":
        valid_values = ["rare", "moderate", "frequent"]
        if value and value in valid_values:
            config['linguistic_profile']['pragmatics']['emojis_usage'] = value
            await update.message.reply_text(f"Emoji usage set to: {value}")
        else:
            current = config['linguistic_profile']['pragmatics'].get('emojis_usage', 'moderate')
            await update.message.reply_text(
                f"Current emoji usage: {current}\n"
                f"Valid options: {', '.join(valid_values)}"
            )
    
    elif trait == "humor_style":
        valid_values = ["dry", "silly", "sarcastic", "dark"]
        if value and value in valid_values:
            config['linguistic_profile']['pragmatics']['humor_style'] = value
            await update.message.reply_text(f"Humor style set to: {value}")
        else:
            current = config['linguistic_profile']['pragmatics'].get('humor_style', 'dry')
            await update.message.reply_text(
                f"Current humor style: {current}\n"
                f"Valid options: {', '.join(valid_values)}"
            )
    
    elif trait == "talkativeness":
        valid_values = ["low", "medium", "high"]
        if value and value in valid_values:
            config['linguistic_profile']['pragmatics']['talkativeness'] = value
            await update.message.reply_text(f"Talkativeness set to: {value}")
        else:
            current = config['linguistic_profile']['pragmatics'].get('talkativeness', 'medium')
            await update.message.reply_text(
                f"Current talkativeness: {current}\n"
                f"Valid options: {', '.join(valid_values)}"
            )
    
    elif trait == "random_reply":
        # Toggle random reply chance
        if value and value.replace('.', '', 1).isdigit():
            chance = float(value)
            if 0 <= chance <= 1:
                config['linguistic_profile']['pragmatics']['random_reply_chance'] = chance
                await update.message.reply_text(f"Random reply chance set to: {chance}")
            else:
                await update.message.reply_text("Random reply chance must be between 0 and 1")
        else:
            current = config['linguistic_profile']['pragmatics'].get('random_reply_chance', 0.05)
            await update.message.reply_text(
                f"Current random reply chance: {current}\n"
                f"Use a value between 0 (never) and 1 (always)"
            )
    
    else:
        await update.message.reply_text(
            "Unknown personality trait. Available options: emoji_usage, humor_style, talkativeness, random_reply"
        )
        return
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f'Personality trait {trait} updated.')

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kick a user from the chat (admin only)"""

    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in group chats.")
        return

    chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    admin_ids = [admin.user.id for admin in chat_admins]
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("Only chat administrators can use this command.")
        return
    
    # Check if a user was specified (via reply or username)
    user_to_kick = None
    reason = "No reason specified."
    
    if update.message.reply_to_message:
        # If the command is a reply to someone's message
        user_to_kick = update.message.reply_to_message.from_user
        # Get reason if provided
        if context.args:
            reason = " ".join(context.args)
    elif context.args:
        # If username is provided as an argument
        username = context.args[0]
        if username.startswith('@'):
            username = username[1:]  # Remove @ symbol
        
        # There's no direct way to get user ID from username (?) in telegram-python-bot
        await update.message.reply_text(
            "Jag kan bara banna användare om du svarar på deras meddelande. "
            "Kicking by username isn't supported due to Telegram API limitations."
        )
        return
    
    if not user_to_kick:
        await update.message.reply_text("svara på ett meddelande från användaren du vill banna")
        return
    
    # Don't allow kicking admins
    if user_to_kick.id in admin_ids:
        await update.message.reply_text("sorry, jag verkar inte kunna banna en admin")
        return
    
    # Don't allow kicking the bot itself
    bot_me = await context.bot.get_me()
    if user_to_kick.id == bot_me.id:
        await update.message.reply_text("jag tänker inte banna mig själv 🤪")
        return

    try:
        # Generate kick message using Anna's personality and lyrics
        kick_line = lyrics_service.get_kick_line()
        
        kick_messages = [
            f"{kick_line} {user_to_kick.first_name} lämnar kanalen!",
            f"Banning {user_to_kick.first_name} so hard! {kick_line}",
            f"{user_to_kick.first_name}, {kick_line.lower()}",
            f"{kick_line} - Removing {user_to_kick.first_name} for: {reason}"
        ]
        kick_message = random.choice(kick_messages)
        
        # Kick the user
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_kick.id)
        
        # Immediately unban so they can rejoin
        await context.bot.unban_chat_member(
            update.effective_chat.id, 
            user_to_kick.id,
            only_if_banned=True
        )
        
        await update.message.reply_text(kick_message)
        print(f"User {user_to_kick.first_name} (ID: {user_to_kick.id}) kicked by {update.effective_user.first_name}")
        
    except Exception as e:
        await update.message.reply_text(f"Failed to kick user: {str(e)}")
        print(f"Failed to kick user: {str(e)}")

def register_command_handlers(bot):
    """Register all command handlers with the bot application"""
    handlers = [
        ("hello", hello),
        ("weather", weather_command),
        ("roll", roll_command),
        ("google", googlar),
        ("timer", start_timer),
        ("add", add_to_list),
        ("remove", remove_from_list),
        ("clear", clear_list),
        ("display", display_list),
        ("pollen", pollenrapport),
        ("gmt", time_convert),
        # NLP-enabled commands
        ("chat", chat_with_anna),
        ("status", bot_status),
        ("personality", toggle_personality),
        ("kick", kick_user),
    ]

    # Register command handlers
    for command, callback in handlers:
        bot.add_handler(CommandHandler(command, callback))
    
    return bot