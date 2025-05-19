import os
from dotenv import load_dotenv

load_dotenv()

def get_env_vars():
    """
    Returns:
        tuple: TOKEN, CHAT_ID, WEATHER_KEY, OPENAI_KEY, GOOGLE_KEY, GITHUB_TOKEN
    """
    required_vars = [
        'TELEGRAM_TOKEN', 
        'TELEGRAM_CHAT_ID',
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please check your .env file."
        )

    return (
        os.getenv('TELEGRAM_TOKEN'),
        os.getenv('TELEGRAM_CHAT_ID'),
        os.getenv('OPENWEATHERMAP_API_KEY'),    # Optional for weather functionality
        os.getenv('OPENAI_API_KEY', ''),        # Optional for basic functionality
        os.getenv('GOOGLE_API_KEY', ''),        # Optional for pollen functionality
        os.getenv('GITHUB_TOKEN', '')           # Optional for GitHub functionality
    )