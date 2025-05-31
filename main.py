import logging
import os
import atexit
import sys
from utils.env_utils import validate_required_vars
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers.command_handlers import register_command_handlers
from handlers.message_handlers import handle_message
from handlers.scheduled_tasks import schedule_tasks
from services.scheduler_service import scheduler_service
from services.nlp_service import save_chat_histories
from services.reputation_service import reputation_service
from services.user_service import user_service

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def cleanup_on_exit():
    try:
        save_chat_histories()
        logger.info("Chat histories saved")

        reputation_service._save_reputation()
        logger.info("Reputation data saved")

        user_service._save_users()
        logger.info("User data saved")

        print("All data saved successfully!")
    except Exception as e:
        logger.error(f"Error saving data during shutdown: {e}")
        print(f"Error saving data: {e}")

def validate_environment():
    try:
        validate_required_vars()
        logger.info("Environment variables validated successfully")
        return True
    except EnvironmentError as e:
        logger.error(f"Environment validation failed: {e}")
        print(f"{e}")
        print("\n Required environment variables:")
        print("  - TELEGRAM_TOKEN")
        print("  - TELEGRAM_CHAT_ID")
        print("  - OPENWEATHERMAP_API_KEY")
        print("\n Copy .env.example to .env and fill in your API keys")
        return False

def create_missing_directories():
    """Create necessary directories if needed"""
    directories = [
        'data',
        'config'
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def check_configuration_files():
    required_files = [
        'config/character_config.json'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        logger.warning(f"Missing configuration files: {missing_files}")
        print(f"Missing configuration files: {', '.join(missing_files)}")
        print("The bot may not work properly without these files. Check the documentation for how to create them.")
        return False

    return True

def main():
    atexit.register(cleanup_on_exit)

    if not validate_environment():
        sys.exit(1)

    create_missing_directories()

    check_configuration_files()

    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        print("TELEGRAM_TOKEN not found")
        sys.exit(1)

    try:
        logger.info("Building app...")
        bot = ApplicationBuilder().token(TOKEN).build()

        logger.info("Registering command handlers...")
        register_command_handlers(bot)

        logger.info("Registering message handlers...")
        bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Setting up scheduled tasks...")
        schedule_tasks(bot)
        scheduler_service.schedule_jobs(bot.job_queue)

        print("[+] All required environment variables are set")
        print("[+] Bot configuration complete")
        print("[+] Bot is running. Press Ctrl+C to stop.")
        print("[+] Bot is now active and ready to receive messages!")

        bot.run_polling(
            allowed_updates=['message', 'edited_message', 'channel_post', 'edited_channel_post'],
            drop_pending_updates=True  # Ignore old messages on startup
        )

    except KeyboardInterrupt:
        print("\n Shutting down...")
        logger.info("Bot shutdown initiated by user")

    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
        print(f"Fatal error: {e}")
        print("Check the logs for more details")
        sys.exit(1)

    finally:
        print("Bot shutdown complete")
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    main()