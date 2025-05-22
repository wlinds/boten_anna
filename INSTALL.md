# Boten Anna - Installation & Upgrade Guide

This guide will help you set up Boten Anna with NLP capabilities or upgrade from a previous version.

## Prerequisites

- Python 3.8+
- A Telegram Bot Token (from BotFather)
- An OpenAI API key
- A Google API key (for Pollen API)
- An OpenWeatherMap API key

## Dependencies

Make sure you have the following Python packages installed:

```bash
pip install python-telegram-bot==20.4 requests numpy bs4 openai python-dotenv
```

## Fresh Installation

1. **Clone the repository or download the source code**

2. **Set up your environment variables**
   Create a file named `.env` with the following structure:

   ```env
   # Telegram Bot credentials
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here

   # API Keys
   OPENWEATHERMAP_API_KEY=your_openweathermap_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

3. **Verify the file structure**
   Make sure you have the following files:
   - updated_main.py (main bot code)
   - openai_integration.py (OpenAI integration)
   - improved_pollen.py (Pollen API integration)
   - personality_trainer.py (Personality learning system)
   - character_config.json (Character configuration)
   - env_utils.py (Environment variable utilities)
   - misc.py (Utility functions)
   - time_conversions.py (Time conversion utilities)
   - sr.py (Sveriges Radio API)
   - .env (Your environment variables)

4. **Run the bot**
   ```bash
   python updated_main.py
   ```

## Upgrading from Previous Version

If you had a previous version of Boten Anna without NLP capabilities, follow these steps to upgrade:

1. **Back up your existing files**
   Make a copy of your `main.py` and any other files you've customized.

2. **Create a .env file**
   Convert your existing keys.json to a .env file with the following format:
   ```env
   # Telegram Bot credentials
   TELEGRAM_TOKEN=your-existing-token
   TELEGRAM_CHAT_ID=your-existing-chat-id

   # API Keys
   OPENWEATHERMAP_API_KEY=your-existing-weather-api-key
   OPENAI_API_KEY=your-new-openai-api-key
   GOOGLE_API_KEY=your-new-google-api-key
   GITHUB_TOKEN=your-github-token
   ```

3. **Copy the new files**
   - Copy the new files to your project directory:
     - updated_main.py
     - openai_integration.py
     - improved_pollen.py
     - personality_trainer.py
     - character_config.json
     - env_utils.py

4. **Merge any customizations**
   If you made custom changes to the original bot code, you'll need to manually merge them into the new updated_main.py file.

5. **Install additional dependencies**
   ```bash
   pip install openai python-dotenv
   ```

6. **Run the upgraded bot**
   ```bash
   python updated_main.py
   ```

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

### Command Parameters

Most commands accept parameters, such as:

- `/weather gothenburg` - Check weather in Gothenburg
- `/roll 20` - Roll a 20-sided die
- `/pollen stockholm` - Check pollen levels in Stockholm
- `/personality emoji_usage frequent` - Set emoji usage to "frequent"

## Contact & Support

If you encounter any issues or have questions, please create an issue on the GitHub repository or contact the maintainers directly.