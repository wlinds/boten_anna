<br><br>
<blockquote>

*Jag känner en bot, hon heter Anna, Anna heter hon\
Och hon kan banna, banna dig så hårt\
Hon röjer upp i våran kanal\
Jag vill berätta för dig, att jag känner en bot~*

</blockquote>
<br>

## **Boten Anna** 💁‍♀️

This Telegram group chat bot implement asynchronous functions, allowing for concurrent execution of multiple tasks without blocking the program's execution. The <a href="https://docs.python-telegram-bot.org/en/stable/telegram.ext.html">telegram.ext library</a> builds upon the <a href="https://docs.python.org/3/library/asyncio.html">asyncio library</a> to handle asynchronous operations. 

The bot is enhanced with OpenAI integration to provide natural language understanding and personality capabilities, making it conversational and responsive to users.

> ⚠️ Update TELEGRAM_CHAT_ID after Group Migration
>
>If your Telegram group is migrated to a supergroup, the chat ID will change (it will typically become a larger negative number starting with -100). When this happens, you must update the TELEGRAM_CHAT_ID in your .env to the new value. More info: https://core.telegram.org/api/channel#supergroups

## **Available commands**

| NLP and AI Commands | Description       |
|----------|---------------------------------|
|`/chat {message}`| Directly chat with Anna (Legacy) |
|`/status` | View Anna's personality stats and learning progress |
|`/personality {trait} {value}` | Adjust Anna's personality traits: emoji_usage, humor_style, talkativeness, random_reply |
|`/kick` | (Admin only) Kick a user from the chat with a personalized message from Anna |

| General commands            | Description                                                                                         |
|--------------------|-----------------------------------------------------------------------------------------------------|
| `/hello`           | Greets the user with a Swedish greeting that varies based on time of day.                                                                                   |
| `/roll {dice sides}`            | When members of a group have equal claims to something—such as a piece of loot or a chest— they can roll for it; the player who rolls the highest number is the winner. Defaults to 100.         |
| `/weather {city}`  | Get weather data through OpenWeatherMap API for any city.                                         |
| `/google {query}`  | Get search results for any query using Google.                                        |
| `/timer {seconds}`  | A timer, a companion in our quest to tame chaos and find moments of rest. It guards our tasks, swift and keen, empowering focus, a serene routine. **TODO:** Handle min and hours as well.     
| `/pollen {location}` | Displays pollen levels and forecasts for a specified location (defaults to Gothenburg). Integrates with Google's Pollen API.
| `/gmt {timezone} {hh:mm}` | Converts time from specified timezone to GMT+2 (Sweden time)

| List commands | Description       |
|----------|---------------------------------|
|`/add {item}`    | Add an item to the list
|`/remove {item}` | Remove an item from the list
|`/clear`         | Clear the entire list
|`/display`       | Display all items in the list

**TODO:** Name lists & support creation of multiple lists.

## **Key Features**

### **1. Personality System**

Anna now has a unique personality based on a customizable character configuration. The personality profile includes:

- Demographics (age, location, etc.)
- Linguistic profile (speaking style, common phrases)
- Behavioral traits
- Emotional responses
- Conversation styles

The personality can evolve over time as Anna learns from interactions with users in the chat.

### **2. Natural Language Processing**

Anna can now:
- Respond naturally to mentions of her name
- Learn from conversations to improve her responses
- Make occasional random comments based on a configurable chance
- Detect patterns in language and adapt her communication style
- Track conversation topics and user preferences

### **3.Pollen Reporting**

The bot now integrates with Google's Pollen API to provide detailed pollen forecasts for multiple cities, including:
- Current pollen levels by type
- 3-day forecasts
- Health recommendations
- Visual indicators with emojis

### **4. Moderation Tools**

As referenced in the original "Boten Anna" song, Anna can now actually "ban people so hard":
- Kick users from the group with custom messages
- Detect potential spam behavior
- Warn users about excessive message frequency
- Help keep the chat organized

## **Setup**

**1. Install necessary dependencies:**
```bash
pip install python-telegram-bot requests lxml numpy bs4 openai python-dotenv
```

**2. Get your keys and tokens:**
- Head over to <a href="https://openweathermap.org">OpenWeatherMap</a> to retrieve a free API key.
- Get an OpenAI API key from <a href="https://platform.openai.com/">OpenAI</a>.
- Get a Google API key and enable the Pollen API and Custom Search API.

- Get your Telegram chat_id for the chat you want to add the bot to:
    - open web.telegram in browser
    - right click on the group name on the left menu
    - click 'inspect' button
    - you will see the group id in the attribute data-peer-id="-xxxxxxxxxx" or peer="-xxxxxxxxxx"

- With your Telegram account, execute <code>/new_bot</code> to user <code>@BotFather</code>. Copy the token to access the Telegram HTTP API.

**3. Create your environment file:**\
Create a file named `.env` in the same directory as the Python script and fill in the information:

```
# Telegram Bot credentials
TELEGRAM_TOKEN=your-telegram-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here

# API Keys
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
GITHUB_TOKEN=your-github-token-here
```

**4. Run main.py and start chatting with your new bot!**

# 🤖 - hellö

## **How Personality Learning Works**

The bot employs a personality learning system that:

1. **Records chat patterns** - Tracks greeting styles, emoji usage, topics of interest
2. **Analyzes interactions** - Studies which topics get the most engagement
3. **Adapts gradually** - Updates the character configuration based on interaction patterns
4. **Remembers user preferences** - Tracks frequently discussed topics and adjusts accordingly

You can view the learning progress using the `/status` command and manually adjust traits with `/personality`.

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'openai'"**
   - Run `pip install openai` to install the OpenAI Python package.

2. **"ModuleNotFoundError: No module named 'dotenv'"**
   - Run `pip install python-dotenv` to install the python-dotenv package.

3. **"openai.error.AuthenticationError: Incorrect API key provided"**
   - Check your OpenAI API key in the .env file is valid and has not expired.

4. **"FileNotFoundError: [Errno 2] No such file or directory: '.env'"**
   - Make sure you've created the .env file in the same directory as the script.
   - You can copy .env.example to .env and fill in your API keys.

5. **"TelegramError: Bad Request: not enough rights to ban/unban user"**
   - The bot needs to be an administrator in the chat to kick users.
   - Make sure the bot has the appropriate permissions in the group.

6. **"Error getting pollen data: API error: 403"**
   - Your Google API key may not have the Pollen API enabled.
   - Go to the Google Cloud Console, find your project, and enable the Pollen API.

### API Key Setup Help

#### OpenAI API
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to "API Keys" in your account
4. Create a new secret key
5. Copy the key to your keys.json file

#### Google Pollen API
1. Go to https://console.cloud.google.com/
2. Create a new project or select an existing one
3. Search for "Pollen API" in the API Library
4. Enable the API
5. Go to Credentials and create an API key
6. Copy the key to your keys.json file

## Configuration Options

### Personality Configuration

You can modify the bot's personality by editing `character_config.json`. Key areas to customize:

- `demographics`: Basic information about the bot
- `linguistic_profile`: How the bot talks and communicates
- `pragmatics`: Conversation style and emoji usage
- `psychographics`: Values, fears, and motivations

## **Future Improvements**

- Support for multiple named lists
- Integration with image generation APIs
- Voice message processing
- Integration with more external APIs for enhanced functionality
- M̵̙͠a̸͓̕k̵̖̊e̴̛͚ ̵̤̈h̷͍̏e̵̗̕r̵̯͠ ̶̺͐s̴͕͝ḙ̷̌ṇ̸̔t̴̬͂i̴̫̍e̸̞̓n̵͉̽t̵̰̿