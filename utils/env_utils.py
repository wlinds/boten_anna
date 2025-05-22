import os
from dotenv import load_dotenv
from typing import Optional

# Only load .env file if it exists (for local development)
if os.path.exists('.env'):
    load_dotenv()

def get_required_env(var_name: str) -> str:
    """Get a required environment variable, raise error if missing"""
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")
    return value

def get_optional_env(var_name: str, default_value: str = "") -> str:
    """Get an optional environment variable with a default value"""
    return os.getenv(var_name, default_value)

def validate_required_vars():
    """Validate all required environment variables (call this only when needed)"""
    required_vars = [
        'TELEGRAM_TOKEN', 
        'TELEGRAM_CHAT_ID',
        'OPENWEATHERMAP_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

# Legacy / backward compatibility
def get_env_vars():
    """Legacy function - validates and returns all vars"""
    validate_required_vars()
    return (
        get_required_env('TELEGRAM_TOKEN'),
        get_required_env('TELEGRAM_CHAT_ID'),
        get_required_env('OPENWEATHERMAP_API_KEY'),
        get_optional_env('OPENAI_API_KEY'),
        get_optional_env('GOOGLE_API_KEY'),
        get_optional_env('GITHUB_TOKEN')
    )