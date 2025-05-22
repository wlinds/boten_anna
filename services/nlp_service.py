import os, json, time, random
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.constants import MAX_HISTORY_LENGTH
from data.personality_trainer import personality_trainer
from services.lyrics_service import lyrics_service

def load_character_config():
    """Load the character configuration from file"""
    config_path = os.path.join(os.path.dirname(__file__), '../config/character_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

CHARACTER_CONFIG = load_character_config()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize chat history storage
chat_histories = {} # This stores conversations by chat_id and user_id

def should_respond_randomly() -> bool:
    """Determine if bot should make a random unsolicited reply"""
    random_chance = CHARACTER_CONFIG["linguistic_profile"]["pragmatics"].get("random_reply_chance", 0.0)
    return random.random() < random_chance

def is_bot_mentioned(message_text: str) -> bool:
    """Check if the bot's name is mentioned in the message"""
    name_variations = CHARACTER_CONFIG["demographics"]["name_variations"]
    message_lower = message_text.lower()
    return any(name in message_lower for name in name_variations)

def is_direct_question(message_text: str) -> bool:
    """Determine if a message is a direct question that should be answered"""

    text_lower = message_text.lower()
    has_question_mark = '?' in text_lower
    
    question_starters = [
        'vad', 'hur', 'varför', 'när', 'vem', 'vilken', 'var', 'kan du', 
        'har du', 'what', 'how', 'why', 'when', 'who', 'which', 'where', 
        'can you', 'do you', 'could you', 'would you', 'will you'
    ]
    
    starts_with_question = any(text_lower.startswith(starter) for starter in question_starters)
    
    direct_requests = [
        'berätta', 'tell me', 'say', 'säg', 'visa', 'show', 'ge mig', 'svara', 'give me',
        'help', 'hjälp', 'explain', 'förklara', 'hälsa', 'greet'
    ]
    
    is_request = any(request in text_lower for request in direct_requests)
    
    return has_question_mark or starts_with_question or is_request

def update_chat_history(chat_id: str, user_id: str, role: str, content: str) -> None:
    """Update the chat history with a new message"""
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    chat_histories[chat_id].append({
        "role": role,
        "content": content,
        "user_id": user_id,
        "timestamp": time.time()
    })
    
    # Trim history if too long
    if len(chat_histories[chat_id]) > MAX_HISTORY_LENGTH:
        chat_histories[chat_id] = chat_histories[chat_id][-MAX_HISTORY_LENGTH:]

def get_chat_context(chat_id: str, limit: int = 5) -> List[Dict[str, str]]:
    """Get recent chat history formatted for OpenAI API"""
    if chat_id not in chat_histories:
        return []
    
    # Get recent history and format for NLP API
    recent_history = chat_histories[chat_id][-limit:]
    formatted_history = []
    
    for msg in recent_history:
        role = "assistant" if msg["role"] == "bot" else "user"
        formatted_history.append({
            "role": role,
            "content": msg["content"]
        })
    
    return formatted_history

def create_system_prompt() -> str:
    """Create a system prompt based on the character configuration"""
    config = CHARACTER_CONFIG
    
    system_prompt = config["metadata"]["prompt"] + "\n\n"
    
    # Additional styling instructions for lowercase
    if "rarely starts a sentence with uppercase" in config["linguistic_profile"]["chat_style"].get("grammar_style", []):
        system_prompt += "IMPORTANT: You rarely capitalize the first letter of sentences. Most of your messages should start with lowercase letters.\n\n"
    
    # Add personality traits
    system_prompt += "Your personality traits:\n"
    
    # Add linguistic profile
    linguistics = config["linguistic_profile"]
    system_prompt += f"- You speak with {linguistics['dialect']} and use {linguistics['speech_patterns']['sentence_length']} sentences\n"
    
    # Add greeting variations instruction
    if linguistics['pragmatics'].get('greeting_variation') == "low":
        system_prompt += "- IMPORTANT: Avoid starting messages with standard greetings like 'Hallå' or 'Tjena'. Vary your conversation starters and never start with a greeting.\n"
    
    if linguistics['speech_patterns']['common_phrases']:
        phrases = ", ".join(f'"{phrase}"' for phrase in linguistics['speech_patterns']['common_phrases'])
        system_prompt += f"- You occasionally use phrases like {phrases} or similar.\n"

    if linguistics['speech_patterns']['filler_words']:
        fillers = ", ".join(f'"{filler}"' for filler in linguistics['speech_patterns']['filler_words'])
        system_prompt += f"- You occasionally use filler words like {fillers} and similar.\n"
    
    # Add behavioral traits
    system_prompt += f"- You are {linguistics['pragmatics']['politeness_strategy']} and {linguistics['pragmatics']['humor_style']} in your humor\n"
    
    # Add values and motivations
    if config["psychographics"]["values"]:
        values = ", ".join(config["psychographics"]["values"])
        system_prompt += f"- You value {values}\n"
    
    if config["psychographics"]["motivations"]:
        motivations = ", ".join(config["psychographics"]["motivations"])
        system_prompt += f"- You are motivated by {motivations}\n"
    
    # Remind about emoji usage
    system_prompt += f"- You use emojis {linguistics['pragmatics']['emojis_usage']}\n"
    
    # Add information about command capabilities
    system_prompt += "\nYou have access to the following commands, but should encourage users to use the command format:\n"
    system_prompt += "- /roll [number] - Roll a dice with specified number of sides\n"
    system_prompt += "- /weather [city] - Get weather information\n"
    system_prompt += "- /google [query] - Search Google\n"
    system_prompt += "- /timer [seconds] - Set a timer\n"
    system_prompt += "- /add [item] - Add an item to a list\n"
    system_prompt += "- /remove [item] - Remove an item from the list\n"
    system_prompt += "- /clear - Clear the list\n"
    system_prompt += "- /display - Show the list\n"
    system_prompt += "- /pollen - Show pollen information for any city or region\n"
    system_prompt += "- /gmt [timezone] [time] - Convert time to GMT+2\n"
    
    # Additional moderation capabilities information
    system_prompt += "\nRemember that you can ban spammers from the chat. If someone is spamming, you can mention this."
    
    # Add specific spam handling instructions
    system_prompt += "\n\nSPAM HANDLING:"
    system_prompt += "\nIf you detect a user is spamming (sending many messages quickly), your messages should:"
    system_prompt += "\n1. For Warning #1: Be stern but polite, mention you can 'ban so hard' (referencing the Basshunter song)"
    system_prompt += "\n2. For Warning #2: Be more serious and explicitly tell them to stop spamming or face consequences"
    system_prompt += "\n3. For Warning #3 or higher: Be very direct and mention you will kick them from the chat if they continue"
    system_prompt += "\nUse Swedish phrases like 'jag röjer upp i kanalen' and 'kan banna så hårt' in your warnings."
    
    # Final reminders
    system_prompt += "\n\nIMPORTANT REMINDERS:"
    system_prompt += "\n1. Avoid overused standard greetings like 'Hallå' or 'Tjena' - vary your conversation starters."
    system_prompt += "\n2. When asked to greet someone, do it immediately without waiting for further prompting."
    system_prompt += "\n3. Respond to direct questions, even without your name being explicitly mentioned."
    system_prompt += "\n4. Never use these phrases: 'adventure', 'spill the tea' or 'spill the beans'."
    system_prompt += "\n5. Rarely ask follow up questions."
    
    return system_prompt

def generate_response(chat_id: str, user_id: str, message_text: str, user_name: str) -> str:
    """Generate a response using OpenAI API based on chat history and character configuration"""

    # Check if user is asking about the bot's identity
    if any(phrase in message_text.lower() for phrase in ["vem är du", "who are you", "berätta om dig", "tell me about yourself", "vad är du"]):
        identity_line = lyrics_service.get_identity_line()
        message_text = f"[Respond with a casual introduction that includes this line: {identity_line}] {message_text}"

    # Create conversation context from recent history
    conversation = get_chat_context(chat_id)
    
    system_prompt = create_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history
    messages.extend(conversation)
    
    # Add the current message
    messages.append({
        "role": "user", 
        "content": f"{user_name}: {message_text}"
    })
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.85,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )

        reply = response.choices[0].message.content.strip()
        
        # Additional catch to make sure lowercase patterns are preserved
        if "rarely starts a sentence with uppercase" in CHARACTER_CONFIG["linguistic_profile"]["chat_style"].get("grammar_style", []):
            if random.random() < 0.8:  # 80% chance to use lowercase
                # Find the first letter and make it lowercase
                if reply and reply[0].isalpha() and reply[0].isupper():
                    reply = reply[0].lower() + reply[1:]

        update_chat_history(chat_id, user_id, "user", message_text)
        update_chat_history(chat_id, "bot", "bot", reply)
        
        return reply
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I'm having trouble performing matrix multiplications right now."

def save_chat_histories() -> None:
    data_path = os.path.join(os.path.dirname(__file__), '../data/chat_histories.json')
    with open(data_path, 'w') as f:
        json.dump(chat_histories, f)

    personality_trainer.analyze_chat_history(chat_histories)

def load_chat_histories() -> None:
    """Load chat histories from a file if it exists"""
    global chat_histories
    try:
        data_path = os.path.join(os.path.dirname(__file__), '../data/chat_histories.json')
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                chat_histories = json.load(f)

            personality_trainer.analyze_chat_history(chat_histories)
            
    except Exception as e:
        print(f"Error loading chat histories: {e}")

# Init by loading any existing chat histories
load_chat_histories()